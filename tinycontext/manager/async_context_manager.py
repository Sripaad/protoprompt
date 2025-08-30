"""
AsyncTinyContextManager - Async central orchestrator for the TinyContext system.
"""

import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from ..agents.loader import TinyFactory, TinyPerson
from ..core.async_tiny_world import AsyncTinyWorld, AsyncTinyWorldManager, AgentState, WorkflowStep
from ..core.react_loop import AsyncReActLoop, ReActStep
from ..inference.tensorzero_client import AsyncTensorZeroClient


@dataclass
class AsyncExecutionTrace:
    """Records async execution trace for debugging and analysis."""
    trace_id: str
    task: str
    input_data: Dict[str, Any]
    agents_used: List[str] = field(default_factory=list)
    steps: List[ReActStep] = field(default_factory=list)
    workflow_steps: List[WorkflowStep] = field(default_factory=list)
    output: Optional[str] = None
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for observability."""
        return {
            "trace_id": self.trace_id,
            "task": self.task[:200],  # Truncate for display
            "agents": self.agents_used,
            "step_count": len(self.steps),
            "workflow_step_count": len(self.workflow_steps),
            "success": self.error is None,
            "error": self.error,
            "duration_ms": self.total_duration_ms,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class AsyncTinyContextManager:
    """
    Async central controller that orchestrates the entire TinyContext flow.
    
    Responsibilities:
    - Accept tasks and select appropriate agents
    - Manage FSM state transitions via AsyncTinyWorld
    - Coordinate async ReAct execution loops
    - Handle agent handoffs
    - Track execution traces and sessions
    - Enable concurrent multi-agent workflows
    """
    
    def __init__(self, agents_dir: Optional[str] = None, llm_client: Optional[AsyncTensorZeroClient] = None):
        """
        Initialize the async context manager.
        
        Args:
            agents_dir: Directory containing agent definitions
            llm_client: Async LLM client (TensorZero) for inference
        """
        self.factory = TinyFactory(agents_dir)
        self.world_manager = AsyncTinyWorldManager()
        self.llm_client = llm_client or AsyncTensorZeroClient(use_embedded=False)
        self.react_loop = AsyncReActLoop(self.llm_client)
        
        # Execution tracking
        self.current_traces: Dict[str, AsyncExecutionTrace] = {}
        self.completed_traces: List[AsyncExecutionTrace] = []
        self.sessions: Dict[str, List[AsyncExecutionTrace]] = {}
        
        # Lock for trace management
        self._trace_lock = asyncio.Lock()
        
        # Initialize LLM client
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the async context manager."""
        if not self._initialized:
            await self.llm_client.initialize()
            self._initialized = True
    
    async def run(
        self, 
        task: str, 
        input_data: Dict[str, Any] = None,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Async main execution method - process a task through the system.
        
        Args:
            task: Task description or problem statement
            input_data: Additional input data
            trace_id: Optional trace ID for tracking
            
        Returns:
            Execution result dictionary
        """
        await self.initialize()
        
        # Generate trace ID if not provided (must be UUID v7 for TensorZero)
        if not trace_id:
            import uuid_utils
            trace_id = str(uuid_utils.uuid7())
        
        # Initialize execution trace
        trace = AsyncExecutionTrace(
            trace_id=trace_id,
            task=task,
            input_data=input_data or {}
        )
        
        async with self._trace_lock:
            self.current_traces[trace_id] = trace
        
        try:
            # Select appropriate agent
            agent = await self._select_agent(task, input_data)
            if not agent:
                raise ValueError("No suitable agent found for task")
            
            trace.agents_used.append(agent.name)
            
            # Create or get world for this execution
            world = await self.world_manager.create_world(trace_id)
            
            # Execute task
            result = await self._execute_task(world, agent, task, input_data, trace)
            
            # Complete trace
            trace.output = result
            trace.completed_at = datetime.now()
            trace.total_duration_ms = (trace.completed_at - trace.started_at).total_seconds() * 1000
            
            # Move to completed traces
            async with self._trace_lock:
                if trace_id in self.current_traces:
                    del self.current_traces[trace_id]
                self.completed_traces.append(trace)
            
            return {
                "success": True,
                "output": result,
                "agents": trace.agents_used,
                "trace_id": trace_id,
                "duration_ms": trace.total_duration_ms
            }
            
        except Exception as e:
            # Handle errors
            trace.error = str(e)
            trace.completed_at = datetime.now()
            trace.total_duration_ms = (trace.completed_at - trace.started_at).total_seconds() * 1000
            
            # Move to completed traces
            async with self._trace_lock:
                if trace_id in self.current_traces:
                    del self.current_traces[trace_id]
                self.completed_traces.append(trace)
            
            # Clean up world
            await self.world_manager.remove_world(trace_id)
            
            return {
                "success": False,
                "error": str(e),
                "trace_id": trace_id,
                "duration_ms": trace.total_duration_ms
            }
    
    async def run_concurrent(
        self,
        tasks: List[Tuple[str, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Run multiple tasks concurrently.
        
        Args:
            tasks: List of (task, input_data) tuples
            
        Returns:
            List of execution results
        """
        await self.initialize()
        
        # Create async tasks for concurrent execution
        async_tasks = [
            self.run(task, input_data, f"trace_{i}_{datetime.now().timestamp()}")
            for i, (task, input_data) in enumerate(tasks)
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*async_tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "trace_id": f"trace_{i}_error"
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _select_agent(
        self, 
        task: str, 
        input_data: Dict[str, Any] = None
    ) -> Optional[TinyPerson]:
        """
        Async select the appropriate agent for a task.
        
        Args:
            task: Task description
            input_data: Additional input
            
        Returns:
            Selected TinyPerson agent
        """
        # Use LLM for agent selection if available
        if self.llm_client and self.llm_client.gateway:
            agents = self.factory.list_agents()
            agent_roles = [agent.role for agent in agents]
            
            try:
                selected_role = await self.llm_client.call(
                    function_name="agent_selection",
                    task=task,
                    agents=agent_roles
                )
                
                # Find agent with selected role
                for agent in agents:
                    if agent.role.lower() in selected_role.lower():
                        return agent
            except Exception as e:
                print(f"LLM agent selection failed: {e}, falling back to heuristics")
        
        # Fallback to heuristic-based selection
        task_lower = task.lower()
        
        if "strategy" in task_lower or "strategic" in task_lower:
            agent = self.factory.get_agent_by_role("strategist")
            if agent:
                return agent
        
        if "analyze" in task_lower or "data" in task_lower:
            agent = self.factory.get_agent_by_role("analyzer")
            if agent:
                return agent
        
        if "plan" in task_lower or "project" in task_lower:
            agent = self.factory.get_agent_by_role("planner")
            if agent:
                return agent
        
        # Default to first available agent
        agents = self.factory.list_agents()
        return agents[0] if agents else None
    
    async def _execute_task(
        self,
        world: AsyncTinyWorld,
        agent: TinyPerson,
        task: str,
        input_data: Dict[str, Any],
        trace: AsyncExecutionTrace
    ) -> str:
        """
        Async execute a task with an agent through the FSM.
        
        Args:
            world: The AsyncTinyWorld instance
            agent: The agent to use
            task: Task to execute
            input_data: Additional input
            trace: Execution trace
            
        Returns:
            Execution output
        """
        # Start thinking phase
        workflow_step = await world.start_thinking(agent.name, task)
        trace.workflow_steps.append(workflow_step)
        
        if workflow_step.error:
            raise RuntimeError(f"Failed to start thinking: {workflow_step.error}")
        
        # Execute ReAct step
        context = {"task": task, "input_data": input_data, "world_id": world.world_id}
        react_step = await self.react_loop.execute_step(agent, task, context)
        trace.steps.append(react_step)
        
        # Complete thinking phase
        workflow_step = await world.complete_thinking(react_step.reasoning)
        trace.workflow_steps.append(workflow_step)
        
        if workflow_step.error:
            raise RuntimeError(f"Failed to complete thinking: {workflow_step.error}")
        
        # Check for handoff
        handoff = react_step.metadata.get("handoff") if react_step.metadata else None
        
        # Complete action phase
        workflow_step = await world.complete_acting(react_step.action, handoff)
        trace.workflow_steps.append(workflow_step)
        
        if workflow_step.error:
            raise RuntimeError(f"Failed to complete action: {workflow_step.error}")
        
        if handoff:
            # Find handoff agent
            next_agent = self.factory.get_agent_by_role(handoff)
            if next_agent:
                trace.agents_used.append(next_agent.name)
                
                # Reset world to IDLE for next agent
                await world.reset()
                
                # Recursive execution with new agent
                handoff_task = f"Continue from previous agent's action: {react_step.action}"
                return await self._execute_task(
                    world, next_agent, handoff_task, input_data, trace
                )
            else:
                # No agent found for handoff
                return f"{react_step.action} (Handoff to {handoff} failed - agent not found)"
        else:
            # Task complete
            return react_step.action
    
    async def get_trace(self, trace_id: str) -> Optional[AsyncExecutionTrace]:
        """
        Get a specific execution trace.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            Execution trace or None
        """
        # Check current traces
        if trace_id in self.current_traces:
            return self.current_traces[trace_id]
        
        # Check completed traces
        for trace in self.completed_traces:
            if trace.trace_id == trace_id:
                return trace
        
        return None
    
    async def get_all_traces(self) -> Dict[str, Any]:
        """
        Get all execution traces for observability.
        
        Returns:
            Dictionary with current and completed traces
        """
        return {
            "current": [
                trace.to_dict() for trace in self.current_traces.values()
            ],
            "completed": [
                trace.to_dict() for trace in self.completed_traces[-100:]  # Last 100
            ],
            "total_completed": len(self.completed_traces)
        }
    
    async def get_workflow_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """
        Get detailed workflow trace for a specific execution.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            List of workflow steps
        """
        trace = await self.get_trace(trace_id)
        if not trace:
            return []
        
        return [
            {
                "agent": step.agent_name,
                "state": step.state.value,
                "input": str(step.input_data)[:100],
                "reasoning": step.reasoning[:200] if step.reasoning else "",
                "action": step.action[:200] if step.action else "",
                "error": step.error,
                "timestamp": step.timestamp.isoformat(),
                "duration_ms": step.duration_ms
            }
            for step in trace.workflow_steps
        ]
    
    def get_agent_registry(self) -> List[Dict[str, str]]:
        """
        Get list of available agents.
        
        Returns:
            List of agent information
        """
        return [
            {
                "name": agent.name,
                "role": agent.role,
                "persona": agent.persona
            }
            for agent in self.factory.list_agents()
        ]
    
    async def save_session(self, session_id: str) -> None:
        """
        Save current completed traces to a session.
        
        Args:
            session_id: Session identifier
        """
        async with self._trace_lock:
            self.sessions[session_id] = self.completed_traces.copy()
    
    async def load_session(self, session_id: str) -> List[AsyncExecutionTrace]:
        """
        Load a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of execution traces for the session
        """
        return self.sessions.get(session_id, [])
    
    async def get_observability_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive observability summary.
        
        Returns:
            Dictionary with system metrics and status
        """
        # Get world summaries
        world_summaries = self.world_manager.get_all_world_summaries()
        
        # Calculate metrics
        total_traces = len(self.completed_traces)
        success_count = sum(1 for t in self.completed_traces if not t.error)
        error_count = total_traces - success_count
        
        avg_duration = (
            sum(t.total_duration_ms for t in self.completed_traces) / total_traces
            if total_traces > 0 else 0
        )
        
        # Agent usage statistics
        agent_usage = {}
        for trace in self.completed_traces:
            for agent in trace.agents_used:
                agent_usage[agent] = agent_usage.get(agent, 0) + 1
        
        return {
            "system_status": {
                "active_worlds": len(world_summaries),
                "current_executions": len(self.current_traces),
                "total_completed": total_traces,
                "success_rate": (success_count / total_traces * 100) if total_traces > 0 else 0,
                "avg_duration_ms": avg_duration
            },
            "agent_usage": agent_usage,
            "active_worlds": world_summaries,
            "recent_errors": [
                {"trace_id": t.trace_id, "error": t.error}
                for t in self.completed_traces[-10:]
                if t.error
            ]
        }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.llm_client:
            await self.llm_client.close()