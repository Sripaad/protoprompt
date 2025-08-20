"""
Workflow Definition System for TinyContext with Observability.

This module provides a declarative way to define multi-agent workflows
with built-in observability hooks for TensorZero.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import yaml
import json
from datetime import datetime


class WorkflowNodeType(Enum):
    """Types of nodes in a workflow."""
    AGENT = "agent"           # Agent reasoning/action node
    DECISION = "decision"     # Conditional branching
    PARALLEL = "parallel"     # Parallel execution
    SEQUENTIAL = "sequential" # Sequential execution
    LOOP = "loop"            # Loop until condition
    HANDOFF = "handoff"      # Agent handoff
    TOOL = "tool"            # External tool call
    CHECKPOINT = "checkpoint" # Save state checkpoint


@dataclass
class WorkflowNode:
    """Represents a node in the workflow graph."""
    id: str
    type: WorkflowNodeType
    name: str
    description: str = ""
    
    # Node-specific configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    # For AGENT nodes
    agent_role: Optional[str] = None
    prompt_template: Optional[str] = None
    
    # For DECISION nodes
    condition: Optional[str] = None  # Expression to evaluate
    branches: Dict[str, str] = field(default_factory=dict)  # condition_value -> next_node_id
    
    # For PARALLEL nodes
    parallel_nodes: List[str] = field(default_factory=list)
    
    # For LOOP nodes
    loop_condition: Optional[str] = None
    max_iterations: int = 10
    
    # Observability hooks
    on_enter: Optional[Callable] = None
    on_exit: Optional[Callable] = None
    on_error: Optional[Callable] = None
    
    # Metrics to track
    track_metrics: List[str] = field(default_factory=lambda: ["duration", "tokens_used", "success_rate"])


@dataclass
class WorkflowEdge:
    """Represents an edge between nodes."""
    from_node: str
    to_node: str
    condition: Optional[str] = None  # Optional condition for traversal
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """
    Complete workflow definition with observability.
    """
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    
    # Workflow graph
    nodes: Dict[str, WorkflowNode] = field(default_factory=dict)
    edges: List[WorkflowEdge] = field(default_factory=list)
    entry_node: str = ""
    
    # Global configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Observability configuration
    observability: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "trace_level": "info",  # debug, info, warn, error
        "metrics": {
            "workflow_duration": True,
            "node_durations": True,
            "token_usage": True,
            "error_rate": True,
            "agent_handoffs": True
        },
        "export": {
            "tensorzero": True,
            "opentelemetry": False,
            "custom_endpoints": []
        }
    })
    
    # Workflow-level callbacks
    on_start: Optional[Callable] = None
    on_complete: Optional[Callable] = None
    on_error: Optional[Callable] = None
    
    def add_node(self, node: WorkflowNode) -> None:
        """Add a node to the workflow."""
        self.nodes[node.id] = node
    
    def add_edge(self, from_node: str, to_node: str, condition: Optional[str] = None) -> None:
        """Add an edge between nodes."""
        edge = WorkflowEdge(from_node, to_node, condition)
        self.edges.append(edge)
    
    def get_next_nodes(self, current_node_id: str) -> List[str]:
        """Get the next nodes from the current node."""
        return [edge.to_node for edge in self.edges if edge.from_node == current_node_id]
    
    def validate(self) -> List[str]:
        """Validate the workflow definition."""
        errors = []
        
        # Check entry node exists
        if self.entry_node not in self.nodes:
            errors.append(f"Entry node '{self.entry_node}' not found in nodes")
        
        # Check all edges reference valid nodes
        for edge in self.edges:
            if edge.from_node not in self.nodes:
                errors.append(f"Edge references unknown from_node: {edge.from_node}")
            if edge.to_node not in self.nodes:
                errors.append(f"Edge references unknown to_node: {edge.to_node}")
        
        # Check agent nodes have roles
        for node_id, node in self.nodes.items():
            if node.type == WorkflowNodeType.AGENT and not node.agent_role:
                errors.append(f"Agent node '{node_id}' missing agent_role")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "entry_node": self.entry_node,
            "nodes": {
                node_id: {
                    "id": node.id,
                    "type": node.type.value,
                    "name": node.name,
                    "description": node.description,
                    "config": node.config,
                    "agent_role": node.agent_role,
                    "prompt_template": node.prompt_template,
                    "condition": node.condition,
                    "branches": node.branches,
                    "parallel_nodes": node.parallel_nodes,
                    "loop_condition": node.loop_condition,
                    "max_iterations": node.max_iterations,
                    "track_metrics": node.track_metrics
                }
                for node_id, node in self.nodes.items()
            },
            "edges": [
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "condition": edge.condition,
                    "metadata": edge.metadata
                }
                for edge in self.edges
            ],
            "config": self.config,
            "observability": self.observability
        }
    
    def to_yaml(self) -> str:
        """Export to YAML format."""
        return yaml.dump(self.to_dict(), default_flow_style=False)
    
    def to_json(self) -> str:
        """Export to JSON format."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowDefinition':
        """Create from dictionary."""
        workflow = cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            entry_node=data.get("entry_node", ""),
            config=data.get("config", {}),
            observability=data.get("observability", {})
        )
        
        # Add nodes
        for node_data in data.get("nodes", {}).values():
            node = WorkflowNode(
                id=node_data["id"],
                type=WorkflowNodeType(node_data["type"]),
                name=node_data["name"],
                description=node_data.get("description", ""),
                config=node_data.get("config", {}),
                agent_role=node_data.get("agent_role"),
                prompt_template=node_data.get("prompt_template"),
                condition=node_data.get("condition"),
                branches=node_data.get("branches", {}),
                parallel_nodes=node_data.get("parallel_nodes", []),
                loop_condition=node_data.get("loop_condition"),
                max_iterations=node_data.get("max_iterations", 10),
                track_metrics=node_data.get("track_metrics", ["duration"])
            )
            workflow.add_node(node)
        
        # Add edges
        for edge_data in data.get("edges", []):
            workflow.add_edge(
                edge_data["from"],
                edge_data["to"],
                edge_data.get("condition")
            )
        
        return workflow
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'WorkflowDefinition':
        """Load from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WorkflowDefinition':
        """Load from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class WorkflowBuilder:
    """
    Fluent API for building workflows.
    """
    
    def __init__(self, workflow_id: str, name: str):
        """Initialize workflow builder."""
        self.workflow = WorkflowDefinition(
            id=workflow_id,
            name=name,
            description=""
        )
        self._current_node_id = None
    
    def with_description(self, description: str) -> 'WorkflowBuilder':
        """Set workflow description."""
        self.workflow.description = description
        return self
    
    def with_observability(self, config: Dict[str, Any]) -> 'WorkflowBuilder':
        """Configure observability settings."""
        self.workflow.observability.update(config)
        return self
    
    def add_agent_node(
        self, 
        node_id: str, 
        name: str,
        agent_role: str,
        prompt_template: Optional[str] = None
    ) -> 'WorkflowBuilder':
        """Add an agent node."""
        node = WorkflowNode(
            id=node_id,
            type=WorkflowNodeType.AGENT,
            name=name,
            agent_role=agent_role,
            prompt_template=prompt_template
        )
        self.workflow.add_node(node)
        
        if not self.workflow.entry_node:
            self.workflow.entry_node = node_id
        
        if self._current_node_id:
            self.workflow.add_edge(self._current_node_id, node_id)
        
        self._current_node_id = node_id
        return self
    
    def add_decision_node(
        self,
        node_id: str,
        name: str,
        condition: str,
        branches: Dict[str, str]
    ) -> 'WorkflowBuilder':
        """Add a decision node."""
        node = WorkflowNode(
            id=node_id,
            type=WorkflowNodeType.DECISION,
            name=name,
            condition=condition,
            branches=branches
        )
        self.workflow.add_node(node)
        
        if self._current_node_id:
            self.workflow.add_edge(self._current_node_id, node_id)
        
        # Add edges for branches
        for condition_value, next_node_id in branches.items():
            self.workflow.add_edge(node_id, next_node_id, condition_value)
        
        self._current_node_id = node_id
        return self
    
    def add_parallel_nodes(
        self,
        node_id: str,
        name: str,
        parallel_node_ids: List[str]
    ) -> 'WorkflowBuilder':
        """Add a parallel execution node."""
        node = WorkflowNode(
            id=node_id,
            type=WorkflowNodeType.PARALLEL,
            name=name,
            parallel_nodes=parallel_node_ids
        )
        self.workflow.add_node(node)
        
        if self._current_node_id:
            self.workflow.add_edge(self._current_node_id, node_id)
        
        # Add edges to parallel nodes
        for parallel_id in parallel_node_ids:
            self.workflow.add_edge(node_id, parallel_id)
        
        self._current_node_id = node_id
        return self
    
    def add_loop_node(
        self,
        node_id: str,
        name: str,
        loop_condition: str,
        max_iterations: int = 10
    ) -> 'WorkflowBuilder':
        """Add a loop node."""
        node = WorkflowNode(
            id=node_id,
            type=WorkflowNodeType.LOOP,
            name=name,
            loop_condition=loop_condition,
            max_iterations=max_iterations
        )
        self.workflow.add_node(node)
        
        if self._current_node_id:
            self.workflow.add_edge(self._current_node_id, node_id)
        
        self._current_node_id = node_id
        return self
    
    def connect(self, from_node: str, to_node: str, condition: Optional[str] = None) -> 'WorkflowBuilder':
        """Manually connect two nodes."""
        self.workflow.add_edge(from_node, to_node, condition)
        return self
    
    def build(self) -> WorkflowDefinition:
        """Build and validate the workflow."""
        errors = self.workflow.validate()
        if errors:
            raise ValueError(f"Workflow validation failed: {errors}")
        return self.workflow


# Example workflow definitions
def create_customer_service_workflow() -> WorkflowDefinition:
    """
    Example: Customer service workflow with multiple agents.
    """
    builder = WorkflowBuilder("customer_service_v1", "Customer Service Workflow")
    
    builder.with_description("AI-powered customer service with escalation")
    builder.with_observability({
        "trace_level": "debug",
        "metrics": {
            "customer_satisfaction": True,
            "resolution_time": True,
            "escalation_rate": True
        }
    })
    
    # Define the workflow
    builder.add_agent_node(
        "intake",
        "Customer Intake",
        agent_role="analyzer",
        prompt_template="Analyze customer request: {input}"
    )
    
    builder.add_decision_node(
        "triage",
        "Issue Triage",
        condition="issue_complexity",
        branches={
            "simple": "simple_resolution",
            "complex": "expert_agent",
            "urgent": "escalation"
        }
    )
    
    builder.add_agent_node(
        "simple_resolution",
        "Simple Issue Resolution",
        agent_role="assistant",
        prompt_template="Resolve simple issue: {issue}"
    )
    
    builder.add_agent_node(
        "expert_agent",
        "Expert Resolution",
        agent_role="strategist",
        prompt_template="Provide expert solution for: {issue}"
    )
    
    builder.add_agent_node(
        "escalation",
        "Human Escalation",
        agent_role="planner",
        prompt_template="Prepare escalation summary: {issue}"
    )
    
    # Connect nodes
    builder.connect("intake", "triage")
    builder.connect("simple_resolution", "feedback")
    builder.connect("expert_agent", "feedback")
    builder.connect("escalation", "feedback")
    
    builder.add_agent_node(
        "feedback",
        "Collect Feedback",
        agent_role="analyzer",
        prompt_template="Analyze resolution and collect feedback"
    )
    
    return builder.build()


def create_data_analysis_workflow() -> WorkflowDefinition:
    """
    Example: Data analysis workflow with parallel processing.
    """
    builder = WorkflowBuilder("data_analysis_v1", "Data Analysis Pipeline")
    
    builder.with_description("Parallel data analysis with multiple specialists")
    
    # Initial data ingestion
    builder.add_agent_node(
        "ingest",
        "Data Ingestion",
        agent_role="analyzer",
        prompt_template="Analyze data requirements: {requirements}"
    )
    
    # Parallel analysis
    builder.add_parallel_nodes(
        "parallel_analysis",
        "Parallel Analysis",
        ["statistical_analysis", "pattern_detection", "anomaly_detection"]
    )
    
    builder.add_agent_node(
        "statistical_analysis",
        "Statistical Analysis",
        agent_role="analyzer",
        prompt_template="Perform statistical analysis on {data}"
    )
    
    builder.add_agent_node(
        "pattern_detection",
        "Pattern Detection",
        agent_role="analyzer",
        prompt_template="Detect patterns in {data}"
    )
    
    builder.add_agent_node(
        "anomaly_detection",
        "Anomaly Detection",
        agent_role="analyzer",
        prompt_template="Identify anomalies in {data}"
    )
    
    # Synthesis
    builder.add_agent_node(
        "synthesis",
        "Results Synthesis",
        agent_role="strategist",
        prompt_template="Synthesize analysis results: {results}"
    )
    
    # Connect parallel outputs to synthesis
    builder.connect("statistical_analysis", "synthesis")
    builder.connect("pattern_detection", "synthesis")
    builder.connect("anomaly_detection", "synthesis")
    
    return builder.build()