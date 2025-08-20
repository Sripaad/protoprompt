"""
TinyContextManager - Central orchestrator for the TinyContext system.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

from ..agents.loader import TinyFactory, TinyPerson
from ..core.tiny_world import TinyWorld, AgentState
from ..core.react_loop import ReActLoop, ReActStep


@dataclass
class ExecutionTrace:
    """Records execution trace for debugging and analysis."""
    task: str
    input_data: Dict[str, Any]
    agent_used: str
    steps: List[ReActStep] = field(default_factory=list)
    state_transitions: List[Dict[str, Any]] = field(default_factory=list)
    output: Optional[str] = None
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class TinyContextManager:
    """
    Central controller that orchestrates the entire TinyContext flow.
    
    Responsibilities:
    - Accept tasks and select appropriate agents
    - Manage FSM state transitions via TinyWorld
    - Coordinate ReAct execution loops
    - Handle agent handoffs
    - Track execution traces and sessions
    """
    
    def __init__(self, agents_dir: Optional[str] = None, llm_client=None):
        """
        Initialize the context manager.
        
        Args:
            agents_dir: Directory containing agent definitions
            llm_client: LLM client (TensorZero) for inference
        """
        self.factory = TinyFactory(agents_dir)
        self.world = TinyWorld()
        self.react = ReActLoop(llm_client)
        self.llm_client = llm_client
        
        # Execution tracking
        self.current_trace: Optional[ExecutionTrace] = None
        self.traces: List[ExecutionTrace] = []
        self.sessions: Dict[str, List[ExecutionTrace]] = {}
        
        # Register FSM callbacks
        self._register_fsm_callbacks()
    
    def _register_fsm_callbacks(self) -> None:
        """Register callbacks for FSM state transitions."""
        # Log state transitions
        def log_transition(world):
            if self.current_trace and world.transitions:
                last_transition = world.transitions[-1]
                self.current_trace.state_transitions.append({
                    "from": last_transition.from_state.value,
                    "to": last_transition.to_state.value,
                    "trigger": last_transition.trigger,
                    "timestamp": last_transition.timestamp.isoformat()
                })
        
        for state in AgentState:
            self.world.register_on_enter(state, log_transition)
    
    def run(self, task: str, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main execution method - process a task through the system.
        
        Args:
            task: Task description or problem statement
            input_data: Additional input data
            
        Returns:
            Execution result dictionary
        """
        # Initialize execution trace
        self.current_trace = ExecutionTrace(
            task=task,
            input_data=input_data or {},
            agent_used=""
        )
        
        try:
            # Select appropriate agent
            agent = self._select_agent(task, input_data)
            if not agent:
                raise ValueError("No suitable agent found for task")
            
            self.current_trace.agent_used = agent.name
            
            # Reset FSM
            self.world.reset()
            
            # Start execution
            result = self._execute_task(agent, task, input_data)
            
            # Complete trace
            self.current_trace.output = result
            self.current_trace.completed_at = datetime.now()
            
            # Store trace
            self.traces.append(self.current_trace)
            
            return {
                "success": True,
                "output": result,
                "agent": agent.name,
                "trace_id": len(self.traces) - 1
            }
            
        except Exception as e:
            # Handle errors
            self.world.enter_error(str(e))
            self.current_trace.error = str(e)
            self.current_trace.completed_at = datetime.now()
            self.traces.append(self.current_trace)
            
            return {
                "success": False,
                "error": str(e),
                "trace_id": len(self.traces) - 1
            }
    
    def _select_agent(self, task: str, input_data: Dict[str, Any] = None) -> Optional[TinyPerson]:
        """
        Select the appropriate agent for a task.
        
        Args:
            task: Task description
            input_data: Additional input
            
        Returns:
            Selected TinyPerson agent
        """
        # Simple heuristic-based selection for MVP
        task_lower = task.lower()
        
        if "strategy" in task_lower or "plan" in task_lower:
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
    
    def _execute_task(self, agent: TinyPerson, task: str, input_data: Dict[str, Any] = None) -> str:
        """
        Execute a task with an agent through the FSM.
        
        Args:
            agent: The agent to use
            task: Task to execute
            input_data: Additional input
            
        Returns:
            Execution output
        """
        # Transition to THINKING
        if not self.world.start_thinking(task):
            raise RuntimeError("Failed to start thinking")
        
        # Execute ReAct step
        context = {"task": task, "input_data": input_data}
        step = self.react.execute_step(agent, task, context)
        self.current_trace.steps.append(step)
        
        # Complete thinking phase
        if not self.world.complete_thinking(step.reasoning):
            raise RuntimeError("Failed to complete thinking")
        
        # Complete action phase
        handoff = step.metadata.get("handoff") if step.metadata else None
        
        if handoff:
            # Handle handoff
            if not self.world.complete_action(step.action, handoff):
                raise RuntimeError("Failed to complete action with handoff")
            
            # Find handoff agent
            next_agent = self.factory.get_agent_by_role(handoff)
            if next_agent:
                # Complete handoff
                self.world.complete_handoff()
                
                # Recursive execution with new agent
                handoff_task = f"Continue from: {step.action}"
                return self._execute_task(next_agent, handoff_task, input_data)
            else:
                # No agent found for handoff
                self.world.complete_handoff()
                return f"{step.action} (Handoff to {handoff} failed - agent not found)"
        else:
            # Complete without handoff
            if not self.world.complete_action(step.action):
                raise RuntimeError("Failed to complete action")
            
            return step.action
    
    def load_session(self, session_id: str) -> List[ExecutionTrace]:
        """
        Load a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of execution traces for the session
        """
        return self.sessions.get(session_id, [])
    
    def save_session(self, session_id: str) -> None:
        """
        Save current traces to a session.
        
        Args:
            session_id: Session identifier
        """
        self.sessions[session_id] = self.traces.copy()
    
    def log_trace(self, trace_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get formatted trace log.
        
        Args:
            trace_id: Specific trace ID, or latest if None
            
        Returns:
            Trace information dictionary
        """
        if trace_id is None:
            trace_id = len(self.traces) - 1
        
        if 0 <= trace_id < len(self.traces):
            trace = self.traces[trace_id]
            return {
                "task": trace.task,
                "agent": trace.agent_used,
                "steps": [
                    {
                        "reasoning": step.reasoning,
                        "action": step.action,
                        "confidence": step.confidence
                    }
                    for step in trace.steps
                ],
                "state_transitions": trace.state_transitions,
                "output": trace.output,
                "error": trace.error,
                "duration": (
                    (trace.completed_at - trace.started_at).total_seconds()
                    if trace.completed_at else None
                )
            }
        
        return {"error": "Trace not found"}
    
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
    
    def get_fsm_state(self) -> Dict[str, Any]:
        """
        Get current FSM state information.
        
        Returns:
            FSM state dictionary
        """
        return self.world.get_state_info()