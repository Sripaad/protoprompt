"""
AsyncTinyWorld - Async FSM-based execution engine for TinyPerson agents.
"""

import asyncio
from enum import Enum
from typing import Optional, Any, Dict, Callable, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime


class AgentState(Enum):
    """FSM states for agent execution."""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    HANDING_OFF = "handing_off"
    ERROR = "error"


@dataclass
class StateTransition:
    """Records a state transition."""
    from_state: AgentState
    to_state: AgentState
    trigger: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """Represents a step in a workflow."""
    agent_name: str
    state: AgentState
    input_data: Any
    output_data: Any = None
    reasoning: str = ""
    action: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    error: Optional[str] = None


class AsyncTinyWorld:
    """
    Async state machine engine for TinyPerson execution.
    
    Manages the lifecycle of agent interactions through 5 states:
    - IDLE: Waiting for input
    - THINKING: Processing/reasoning about input
    - ACTING: Executing action based on reasoning
    - HANDING_OFF: Transferring control to another agent
    - ERROR: Error state requiring intervention
    """
    
    def __init__(self, world_id: str = "default"):
        """Initialize the async FSM."""
        self.world_id = world_id
        self.current_state = AgentState.IDLE
        self.transitions: List[StateTransition] = []
        self.workflow_steps: List[WorkflowStep] = []
        self.context: Dict[str, Any] = {}
        self.error_message: Optional[str] = None
        
        # State transition rules
        self.valid_transitions = {
            AgentState.IDLE: [AgentState.THINKING, AgentState.ERROR],
            AgentState.THINKING: [AgentState.ACTING, AgentState.ERROR],
            AgentState.ACTING: [AgentState.IDLE, AgentState.HANDING_OFF, AgentState.ERROR],
            AgentState.HANDING_OFF: [AgentState.IDLE, AgentState.ERROR],
            AgentState.ERROR: [AgentState.IDLE]  # Can recover to IDLE
        }
        
        # Async transition callbacks
        self.on_enter_callbacks: Dict[AgentState, List[Callable]] = {
            state: [] for state in AgentState
        }
        self.on_exit_callbacks: Dict[AgentState, List[Callable]] = {
            state: [] for state in AgentState
        }
        
        # Lock for state transitions
        self._state_lock = asyncio.Lock()
    
    def can_transition(self, to_state: AgentState) -> bool:
        """
        Check if transition to target state is valid.
        
        Args:
            to_state: Target state
            
        Returns:
            True if transition is valid
        """
        return to_state in self.valid_transitions.get(self.current_state, [])
    
    async def transition_to(
        self, 
        to_state: AgentState, 
        trigger: str = "", 
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Async transition to a new state.
        
        Args:
            to_state: Target state
            trigger: What triggered this transition
            metadata: Additional transition metadata
            
        Returns:
            True if transition succeeded
        """
        async with self._state_lock:
            if not self.can_transition(to_state):
                self.error_message = f"Invalid transition from {self.current_state} to {to_state}"
                return False
            
            # Execute async exit callbacks for current state
            for callback in self.on_exit_callbacks[self.current_state]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(self)
                    else:
                        callback(self)
                except Exception as e:
                    print(f"Exit callback error: {e}")
            
            # Record transition
            transition = StateTransition(
                from_state=self.current_state,
                to_state=to_state,
                trigger=trigger,
                metadata=metadata or {}
            )
            self.transitions.append(transition)
            
            # Update state
            old_state = self.current_state
            self.current_state = to_state
            
            # Execute async enter callbacks for new state
            for callback in self.on_enter_callbacks[to_state]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(self)
                    else:
                        callback(self)
                except Exception as e:
                    print(f"Enter callback error: {e}")
            
            return True
    
    async def start_thinking(self, agent_name: str, input_data: Any) -> WorkflowStep:
        """
        Async transition to THINKING state with input.
        
        Args:
            agent_name: Name of the agent
            input_data: Input to process
            
        Returns:
            WorkflowStep recording this transition
        """
        start_time = datetime.now()
        
        if self.current_state != AgentState.IDLE:
            step = WorkflowStep(
                agent_name=agent_name,
                state=self.current_state,
                input_data=input_data,
                error="Cannot start thinking - not in IDLE state"
            )
            self.workflow_steps.append(step)
            return step
        
        self.context["input"] = input_data
        self.context["current_agent"] = agent_name
        
        success = await self.transition_to(
            AgentState.THINKING, 
            "user_input", 
            {"input": input_data, "agent": agent_name}
        )
        
        step = WorkflowStep(
            agent_name=agent_name,
            state=AgentState.THINKING,
            input_data=input_data,
            duration_ms=(datetime.now() - start_time).total_seconds() * 1000
        )
        self.workflow_steps.append(step)
        return step
    
    async def complete_thinking(self, reasoning: str) -> WorkflowStep:
        """
        Async complete thinking and transition to ACTING.
        
        Args:
            reasoning: The reasoning output
            
        Returns:
            WorkflowStep recording this transition
        """
        start_time = datetime.now()
        agent_name = self.context.get("current_agent", "unknown")
        
        if self.current_state != AgentState.THINKING:
            step = WorkflowStep(
                agent_name=agent_name,
                state=self.current_state,
                input_data=self.context.get("input"),
                error="Cannot complete thinking - not in THINKING state"
            )
            self.workflow_steps.append(step)
            return step
        
        self.context["reasoning"] = reasoning
        success = await self.transition_to(
            AgentState.ACTING, 
            "reasoning_complete", 
            {"reasoning": reasoning}
        )
        
        step = WorkflowStep(
            agent_name=agent_name,
            state=AgentState.ACTING,
            input_data=self.context.get("input"),
            reasoning=reasoning,
            duration_ms=(datetime.now() - start_time).total_seconds() * 1000
        )
        self.workflow_steps.append(step)
        return step
    
    async def complete_acting(self, action: str, handoff_to: Optional[str] = None) -> WorkflowStep:
        """
        Async complete acting and transition to IDLE or HANDING_OFF.
        
        Args:
            action: The action taken
            handoff_to: Optional agent to hand off to
            
        Returns:
            WorkflowStep recording this transition
        """
        start_time = datetime.now()
        agent_name = self.context.get("current_agent", "unknown")
        
        if self.current_state != AgentState.ACTING:
            step = WorkflowStep(
                agent_name=agent_name,
                state=self.current_state,
                input_data=self.context.get("input"),
                error="Cannot complete acting - not in ACTING state"
            )
            self.workflow_steps.append(step)
            return step
        
        self.context["action"] = action
        
        if handoff_to:
            self.context["handoff_to"] = handoff_to
            target_state = AgentState.HANDING_OFF
            trigger = "handoff_required"
        else:
            target_state = AgentState.IDLE
            trigger = "action_complete"
        
        success = await self.transition_to(
            target_state,
            trigger,
            {"action": action, "handoff_to": handoff_to}
        )
        
        step = WorkflowStep(
            agent_name=agent_name,
            state=target_state,
            input_data=self.context.get("input"),
            reasoning=self.context.get("reasoning", ""),
            action=action,
            output_data={"handoff_to": handoff_to} if handoff_to else None,
            duration_ms=(datetime.now() - start_time).total_seconds() * 1000
        )
        self.workflow_steps.append(step)
        return step
    
    async def handle_error(self, error_message: str) -> WorkflowStep:
        """
        Async transition to ERROR state.
        
        Args:
            error_message: Description of the error
            
        Returns:
            WorkflowStep recording the error
        """
        agent_name = self.context.get("current_agent", "unknown")
        
        self.error_message = error_message
        await self.transition_to(
            AgentState.ERROR,
            "error_occurred",
            {"error": error_message}
        )
        
        step = WorkflowStep(
            agent_name=agent_name,
            state=AgentState.ERROR,
            input_data=self.context.get("input"),
            error=error_message
        )
        self.workflow_steps.append(step)
        return step
    
    async def reset(self) -> None:
        """Async reset to IDLE state."""
        await self.transition_to(AgentState.IDLE, "reset")
        self.context.clear()
        self.error_message = None
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get current state summary for observability.
        
        Returns:
            Dictionary with state information
        """
        return {
            "world_id": self.world_id,
            "current_state": self.current_state.value,
            "context": self.context,
            "error_message": self.error_message,
            "transition_count": len(self.transitions),
            "workflow_step_count": len(self.workflow_steps),
            "last_transition": self.transitions[-1] if self.transitions else None
        }
    
    def get_workflow_trace(self) -> List[Dict[str, Any]]:
        """
        Get workflow trace for observability.
        
        Returns:
            List of workflow steps as dictionaries
        """
        return [
            {
                "agent": step.agent_name,
                "state": step.state.value,
                "input": str(step.input_data)[:100],  # Truncate for display
                "reasoning": step.reasoning[:200] if step.reasoning else "",
                "action": step.action[:200] if step.action else "",
                "error": step.error,
                "timestamp": step.timestamp.isoformat(),
                "duration_ms": step.duration_ms
            }
            for step in self.workflow_steps
        ]
    
    async def register_callback(
        self, 
        state: AgentState, 
        callback: Callable, 
        on_enter: bool = True
    ) -> None:
        """
        Register an async callback for state transitions.
        
        Args:
            state: State to register callback for
            callback: Async callback function
            on_enter: True for enter callback, False for exit
        """
        if on_enter:
            self.on_enter_callbacks[state].append(callback)
        else:
            self.on_exit_callbacks[state].append(callback)


class AsyncTinyWorldManager:
    """
    Manager for multiple concurrent AsyncTinyWorld instances.
    
    Enables running multiple agent workflows in parallel.
    """
    
    def __init__(self):
        """Initialize the world manager."""
        self.worlds: Dict[str, AsyncTinyWorld] = {}
        self._world_lock = asyncio.Lock()
    
    async def create_world(self, world_id: str) -> AsyncTinyWorld:
        """
        Create a new world instance.
        
        Args:
            world_id: Unique identifier for the world
            
        Returns:
            New AsyncTinyWorld instance
        """
        async with self._world_lock:
            if world_id in self.worlds:
                raise ValueError(f"World {world_id} already exists")
            
            world = AsyncTinyWorld(world_id)
            self.worlds[world_id] = world
            return world
    
    async def get_world(self, world_id: str) -> Optional[AsyncTinyWorld]:
        """
        Get an existing world instance.
        
        Args:
            world_id: World identifier
            
        Returns:
            AsyncTinyWorld instance or None
        """
        return self.worlds.get(world_id)
    
    async def remove_world(self, world_id: str) -> bool:
        """
        Remove a world instance.
        
        Args:
            world_id: World identifier
            
        Returns:
            True if removed, False if not found
        """
        async with self._world_lock:
            if world_id in self.worlds:
                del self.worlds[world_id]
                return True
            return False
    
    async def execute_parallel_workflows(
        self,
        workflows: List[Tuple[str, Any]]
    ) -> List[List[WorkflowStep]]:
        """
        Execute multiple workflows in parallel.
        
        Args:
            workflows: List of (world_id, input_data) tuples
            
        Returns:
            List of workflow traces
        """
        tasks = []
        
        for world_id, input_data in workflows:
            # Create world if needed
            if world_id not in self.worlds:
                await self.create_world(world_id)
            
            world = self.worlds[world_id]
            # This would typically call a full workflow execution
            # For now, just simulate with state transitions
            tasks.append(self._execute_single_workflow(world, input_data))
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def _execute_single_workflow(
        self, 
        world: AsyncTinyWorld, 
        input_data: Any
    ) -> List[WorkflowStep]:
        """
        Execute a single workflow (placeholder for full implementation).
        
        Args:
            world: World instance
            input_data: Input for the workflow
            
        Returns:
            List of workflow steps
        """
        # This is a simplified example - real implementation would
        # integrate with agents and ReAct loop
        await world.start_thinking("agent1", input_data)
        await asyncio.sleep(0.1)  # Simulate processing
        await world.complete_thinking("Analyzed the input")
        await world.complete_acting("Executed action")
        
        return world.workflow_steps
    
    def get_all_world_summaries(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summaries of all worlds for observability.
        
        Returns:
            Dictionary of world summaries
        """
        return {
            world_id: world.get_state_summary()
            for world_id, world in self.worlds.items()
        }