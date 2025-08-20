"""
Workflow Executor with Observability Integration.

Executes workflow definitions with full observability through TensorZero.
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json

from .workflow_definition import (
    WorkflowDefinition, 
    WorkflowNode, 
    WorkflowNodeType,
    WorkflowEdge
)
from ..manager.async_context_manager import AsyncTinyContextManager
from ..inference.tensorzero_client import AsyncTensorZeroClient


class NodeExecutionStatus(Enum):
    """Status of node execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeExecutionResult:
    """Result of executing a workflow node."""
    node_id: str
    status: NodeExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    output: Any = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for observability."""
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "output": str(self.output)[:500] if self.output else None,  # Truncate
            "error": self.error,
            "metrics": self.metrics
        }


@dataclass
class WorkflowExecutionContext:
    """Context for workflow execution."""
    workflow_id: str
    execution_id: str
    input_data: Dict[str, Any]
    variables: Dict[str, Any] = field(default_factory=dict)
    node_results: Dict[str, NodeExecutionResult] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_duration_ms: float = 0.0
    status: str = "running"
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a variable from context."""
        return self.variables.get(key, default)
    
    def set_variable(self, key: str, value: Any) -> None:
        """Set a variable in context."""
        self.variables[key] = value
    
    def get_node_output(self, node_id: str) -> Any:
        """Get output from a previously executed node."""
        if node_id in self.node_results:
            return self.node_results[node_id].output
        return None
    
    def to_observability_trace(self) -> Dict[str, Any]:
        """Convert to observability trace format."""
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.total_duration_ms,
            "input_data": self.input_data,
            "variables": self.variables,
            "node_executions": [
                result.to_dict() for result in self.node_results.values()
            ],
            "metrics": {
                "total_nodes": len(self.node_results),
                "successful_nodes": sum(
                    1 for r in self.node_results.values() 
                    if r.status == NodeExecutionStatus.COMPLETED
                ),
                "failed_nodes": sum(
                    1 for r in self.node_results.values() 
                    if r.status == NodeExecutionStatus.FAILED
                ),
                "avg_node_duration_ms": (
                    sum(r.duration_ms for r in self.node_results.values()) / len(self.node_results)
                    if self.node_results else 0
                )
            }
        }


class WorkflowExecutor:
    """
    Executes workflow definitions with full observability.
    """
    
    def __init__(
        self,
        context_manager: Optional[AsyncTinyContextManager] = None,
        llm_client: Optional[AsyncTensorZeroClient] = None
    ):
        """
        Initialize workflow executor.
        
        Args:
            context_manager: Async context manager for agent execution
            llm_client: LLM client for inference
        """
        self.context_manager = context_manager or AsyncTinyContextManager()
        self.llm_client = llm_client or self.context_manager.llm_client
        
        # Execution tracking
        self.active_executions: Dict[str, WorkflowExecutionContext] = {}
        self.completed_executions: List[WorkflowExecutionContext] = []
        
        # Lock for execution management
        self._execution_lock = asyncio.Lock()
    
    async def execute(
        self,
        workflow: WorkflowDefinition,
        input_data: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> WorkflowExecutionContext:
        """
        Execute a workflow asynchronously.
        
        Args:
            workflow: Workflow definition to execute
            input_data: Input data for the workflow
            execution_id: Optional execution ID
            
        Returns:
            Workflow execution context with results
        """
        # Validate workflow
        errors = workflow.validate()
        if errors:
            raise ValueError(f"Invalid workflow: {errors}")
        
        # Create execution context
        if not execution_id:
            execution_id = f"exec_{workflow.id}_{datetime.now().timestamp()}"
        
        context = WorkflowExecutionContext(
            workflow_id=workflow.id,
            execution_id=execution_id,
            input_data=input_data
        )
        
        # Track active execution
        async with self._execution_lock:
            self.active_executions[execution_id] = context
        
        try:
            # Execute workflow starting from entry node
            await self._execute_node(workflow, workflow.entry_node, context)
            
            # Complete execution
            context.completed_at = datetime.now()
            context.total_duration_ms = (
                (context.completed_at - context.started_at).total_seconds() * 1000
            )
            context.status = "completed"
            
        except Exception as e:
            # Handle execution error
            context.completed_at = datetime.now()
            context.total_duration_ms = (
                (context.completed_at - context.started_at).total_seconds() * 1000
            )
            context.status = "failed"
            context.set_variable("error", str(e))
            
        finally:
            # Move to completed executions
            async with self._execution_lock:
                if execution_id in self.active_executions:
                    del self.active_executions[execution_id]
                self.completed_executions.append(context)
            
            # Send observability data
            await self._send_observability_data(workflow, context)
        
        return context
    
    async def _execute_node(
        self,
        workflow: WorkflowDefinition,
        node_id: str,
        context: WorkflowExecutionContext
    ) -> NodeExecutionResult:
        """
        Execute a single workflow node.
        
        Args:
            workflow: Workflow definition
            node_id: Node to execute
            context: Execution context
            
        Returns:
            Node execution result
        """
        if node_id not in workflow.nodes:
            raise ValueError(f"Node {node_id} not found in workflow")
        
        node = workflow.nodes[node_id]
        
        # Check if already executed
        if node_id in context.node_results:
            return context.node_results[node_id]
        
        # Create result object
        result = NodeExecutionResult(
            node_id=node_id,
            status=NodeExecutionStatus.RUNNING,
            started_at=datetime.now()
        )
        
        try:
            # Execute based on node type
            if node.type == WorkflowNodeType.AGENT:
                output = await self._execute_agent_node(node, context)
            elif node.type == WorkflowNodeType.DECISION:
                output = await self._execute_decision_node(workflow, node, context)
            elif node.type == WorkflowNodeType.PARALLEL:
                output = await self._execute_parallel_node(workflow, node, context)
            elif node.type == WorkflowNodeType.SEQUENTIAL:
                output = await self._execute_sequential_node(workflow, node, context)
            elif node.type == WorkflowNodeType.LOOP:
                output = await self._execute_loop_node(workflow, node, context)
            else:
                output = f"Unsupported node type: {node.type}"
            
            # Complete result
            result.output = output
            result.status = NodeExecutionStatus.COMPLETED
            result.completed_at = datetime.now()
            result.duration_ms = (
                (result.completed_at - result.started_at).total_seconds() * 1000
            )
            
            # Store output in context
            context.set_variable(f"{node_id}_output", output)
            
        except Exception as e:
            # Handle node execution error
            result.error = str(e)
            result.status = NodeExecutionStatus.FAILED
            result.completed_at = datetime.now()
            result.duration_ms = (
                (result.completed_at - result.started_at).total_seconds() * 1000
            )
        
        # Store result
        context.node_results[node_id] = result
        
        # Execute next nodes if successful
        if result.status == NodeExecutionStatus.COMPLETED:
            next_nodes = workflow.get_next_nodes(node_id)
            for next_node_id in next_nodes:
                await self._execute_node(workflow, next_node_id, context)
        
        return result
    
    async def _execute_agent_node(
        self,
        node: WorkflowNode,
        context: WorkflowExecutionContext
    ) -> Any:
        """Execute an agent node."""
        # Prepare task from template
        task = node.prompt_template or f"Execute {node.name}"
        
        # Replace variables in template
        for key, value in context.variables.items():
            task = task.replace(f"{{{key}}}", str(value))
        
        # Replace input reference
        task = task.replace("{input}", json.dumps(context.input_data))
        
        # Execute through context manager
        result = await self.context_manager.run(
            task=task,
            input_data=context.input_data,
            trace_id=f"{context.execution_id}_{node.id}"
        )
        
        if result["success"]:
            return result["output"]
        else:
            raise RuntimeError(f"Agent execution failed: {result['error']}")
    
    async def _execute_decision_node(
        self,
        workflow: WorkflowDefinition,
        node: WorkflowNode,
        context: WorkflowExecutionContext
    ) -> Any:
        """Execute a decision node."""
        # Evaluate condition
        condition_result = self._evaluate_condition(node.condition, context)
        
        # Find matching branch
        next_node_id = node.branches.get(str(condition_result))
        
        if next_node_id:
            # Execute the selected branch
            await self._execute_node(workflow, next_node_id, context)
            return f"Branched to {next_node_id} based on condition: {condition_result}"
        else:
            return f"No branch for condition result: {condition_result}"
    
    async def _execute_parallel_node(
        self,
        workflow: WorkflowDefinition,
        node: WorkflowNode,
        context: WorkflowExecutionContext
    ) -> Any:
        """Execute parallel nodes concurrently."""
        # Create tasks for parallel execution
        tasks = [
            self._execute_node(workflow, node_id, context)
            for node_id in node.parallel_nodes
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect outputs
        outputs = {}
        for node_id, result in zip(node.parallel_nodes, results):
            if isinstance(result, Exception):
                outputs[node_id] = f"Error: {result}"
            else:
                outputs[node_id] = result.output if hasattr(result, 'output') else result
        
        return outputs
    
    async def _execute_sequential_node(
        self,
        workflow: WorkflowDefinition,
        node: WorkflowNode,
        context: WorkflowExecutionContext
    ) -> Any:
        """Execute nodes sequentially."""
        outputs = []
        
        for node_id in node.config.get("sequence", []):
            result = await self._execute_node(workflow, node_id, context)
            outputs.append(result.output if hasattr(result, 'output') else result)
        
        return outputs
    
    async def _execute_loop_node(
        self,
        workflow: WorkflowDefinition,
        node: WorkflowNode,
        context: WorkflowExecutionContext
    ) -> Any:
        """Execute a loop node."""
        outputs = []
        iterations = 0
        
        while iterations < node.max_iterations:
            # Check loop condition
            if not self._evaluate_condition(node.loop_condition, context):
                break
            
            # Execute loop body (assuming it's defined in config)
            loop_body_node = node.config.get("loop_body")
            if loop_body_node:
                result = await self._execute_node(workflow, loop_body_node, context)
                outputs.append(result.output if hasattr(result, 'output') else result)
            
            iterations += 1
            context.set_variable(f"{node.id}_iteration", iterations)
        
        return {
            "iterations": iterations,
            "outputs": outputs
        }
    
    def _evaluate_condition(
        self,
        condition: str,
        context: WorkflowExecutionContext
    ) -> Any:
        """
        Evaluate a condition expression.
        
        Simple implementation - can be extended with proper expression evaluation.
        """
        if not condition:
            return True
        
        # Replace variables in condition
        for key, value in context.variables.items():
            condition = condition.replace(f"{{{key}}}", str(value))
        
        # Simple evaluation (extend as needed)
        try:
            # WARNING: eval is dangerous - use a proper expression evaluator in production
            # This is just for demonstration
            return eval(condition, {"__builtins__": {}}, context.variables)
        except:
            return condition  # Return as string if evaluation fails
    
    async def _send_observability_data(
        self,
        workflow: WorkflowDefinition,
        context: WorkflowExecutionContext
    ) -> None:
        """
        Send observability data to configured endpoints.
        """
        if not workflow.observability.get("enabled", True):
            return
        
        trace_data = context.to_observability_trace()
        
        # Add workflow metadata
        trace_data["workflow_name"] = workflow.name
        trace_data["workflow_version"] = workflow.version
        
        # Send to TensorZero (already tracked through LLM calls)
        # The individual agent calls are already being tracked
        
        # Log summary
        print(f"Workflow Execution Summary:")
        print(f"  Workflow: {workflow.name} (v{workflow.version})")
        print(f"  Execution ID: {context.execution_id}")
        print(f"  Status: {context.status}")
        print(f"  Duration: {context.total_duration_ms:.2f}ms")
        print(f"  Nodes Executed: {len(context.node_results)}")
        
        # Custom export endpoints
        for endpoint in workflow.observability.get("export", {}).get("custom_endpoints", []):
            # Would send to custom endpoint here
            pass
    
    async def execute_multiple(
        self,
        workflows: List[Tuple[WorkflowDefinition, Dict[str, Any]]]
    ) -> List[WorkflowExecutionContext]:
        """
        Execute multiple workflows concurrently.
        
        Args:
            workflows: List of (workflow, input_data) tuples
            
        Returns:
            List of execution contexts
        """
        tasks = [
            self.execute(workflow, input_data)
            for workflow, input_data in workflows
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed contexts
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                # Create a failed context
                context = WorkflowExecutionContext(
                    workflow_id="error",
                    execution_id=f"error_{datetime.now().timestamp()}",
                    input_data={}
                )
                context.status = "failed"
                context.set_variable("error", str(result))
                processed_results.append(context)
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary of all executions for observability.
        
        Returns:
            Execution summary dictionary
        """
        return {
            "active_executions": len(self.active_executions),
            "completed_executions": len(self.completed_executions),
            "active": [
                {
                    "execution_id": ctx.execution_id,
                    "workflow_id": ctx.workflow_id,
                    "status": ctx.status,
                    "duration_so_far_ms": (
                        (datetime.now() - ctx.started_at).total_seconds() * 1000
                    )
                }
                for ctx in self.active_executions.values()
            ],
            "recent_completed": [
                {
                    "execution_id": ctx.execution_id,
                    "workflow_id": ctx.workflow_id,
                    "status": ctx.status,
                    "duration_ms": ctx.total_duration_ms
                }
                for ctx in self.completed_executions[-10:]  # Last 10
            ]
        }