"""
TinyWorld - FSM-based execution engine for TinyPerson agents.
"""

from enum import Enum
from typing import Optional, Any, Dict, Callable
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


class TinyWorld:
    """
    State machine engine for TinyPerson execution.
    
    Manages the lifecycle of agent interactions through 5 states:
    - IDLE: Waiting for input
    - THINKING: Processing/reasoning about input
    - ACTING: Executing action based on reasoning
    - HANDING_OFF: Transferring control to another agent
    - ERROR: Error state requiring intervention
    """
    
    def __init__(self):
        """Initialize the FSM."""
        self.current_state = AgentState.IDLE
        self.transitions: list[StateTransition] = []
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
        
        # Transition callbacks
        self.on_enter_callbacks: Dict[AgentState, list[Callable]] = {
            state: [] for state in AgentState
        }
        self.on_exit_callbacks: Dict[AgentState, list[Callable]] = {
            state: [] for state in AgentState
        }
    
    def can_transition(self, to_state: AgentState) -> bool:
        """
        Check if transition to target state is valid.
        
        Args:
            to_state: Target state
            
        Returns:
            True if transition is valid
        """
        return to_state in self.valid_transitions.get(self.current_state, [])
    
    def transition_to(self, to_state: AgentState, trigger: str = "", metadata: Dict[str, Any] = None) -> bool:
        """
        Transition to a new state.
        
        Args:
            to_state: Target state
            trigger: What triggered this transition
            metadata: Additional transition metadata
            
        Returns:
            True if transition succeeded
        """
        if not self.can_transition(to_state):
            self.error_message = f"Invalid transition from {self.current_state} to {to_state}"
            return False
        
        # Execute exit callbacks for current state
        for callback in self.on_exit_callbacks[self.current_state]:
            try:
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
        
        # Execute enter callbacks for new state
        for callback in self.on_enter_callbacks[to_state]:
            try:
                callback(self)
            except Exception as e:
                print(f"Enter callback error: {e}")
        
        return True
    
    def start_thinking(self, input_data: Any) -> bool:
        """
        Transition to THINKING state with input.
        
        Args:
            input_data: Input to process
            
        Returns:
            True if transition succeeded
        """
        if self.current_state != AgentState.IDLE:
            return False
        
        self.context["input"] = input_data
        return self.transition_to(AgentState.THINKING, "user_input", {"input": input_data})
    
    def complete_thinking(self, reasoning: str) -> bool:
        """
        Complete thinking and transition to ACTING.
        
        Args:
            reasoning: The reasoning output
            
        Returns:
            True if transition succeeded
        """
        if self.current_state != AgentState.THINKING:
            return False
        
        self.context["reasoning"] = reasoning
        return self.transition_to(AgentState.ACTING, "reasoning_complete", {"reasoning": reasoning})
    
    def complete_action(self, action: str, handoff_to: Optional[str] = None) -> bool:
        """
        Complete action and transition to appropriate state.
        
        Args:
            action: The action taken
            handoff_to: Optional agent to hand off to
            
        Returns:
            True if transition succeeded
        """
        if self.current_state != AgentState.ACTING:
            return False
        
        self.context["action"] = action
        
        if handoff_to:
            self.context["handoff_to"] = handoff_to
            return self.transition_to(
                AgentState.HANDING_OFF, 
                "handoff_requested",
                {"action": action, "handoff_to": handoff_to}
            )
        else:
            return self.transition_to(AgentState.IDLE, "action_complete", {"action": action})
    
    def complete_handoff(self) -> bool:
        """
        Complete handoff and return to IDLE.
        
        Returns:
            True if transition succeeded
        """
        if self.current_state != AgentState.HANDING_OFF:
            return False
        
        return self.transition_to(AgentState.IDLE, "handoff_complete")
    
    def enter_error(self, error: str) -> bool:
        """
        Enter ERROR state with error message.
        
        Args:
            error: Error message
            
        Returns:
            True if transition succeeded
        """
        self.error_message = error
        self.context["error"] = error
        return self.transition_to(AgentState.ERROR, "error_occurred", {"error": error})
    
    def recover_from_error(self) -> bool:
        """
        Recover from ERROR state to IDLE.
        
        Returns:
            True if transition succeeded
        """
        if self.current_state != AgentState.ERROR:
            return False
        
        self.error_message = None
        self.context.pop("error", None)
        return self.transition_to(AgentState.IDLE, "error_recovered")
    
    def reset(self) -> None:
        """Reset the FSM to initial state."""
        self.current_state = AgentState.IDLE
        self.transitions.clear()
        self.context.clear()
        self.error_message = None
    
    def register_on_enter(self, state: AgentState, callback: Callable) -> None:
        """
        Register a callback for entering a state.
        
        Args:
            state: State to register for
            callback: Callback function
        """
        self.on_enter_callbacks[state].append(callback)
    
    def register_on_exit(self, state: AgentState, callback: Callable) -> None:
        """
        Register a callback for exiting a state.
        
        Args:
            state: State to register for
            callback: Callback function
        """
        self.on_exit_callbacks[state].append(callback)
    
    def get_state_info(self) -> Dict[str, Any]:
        """
        Get current state information.
        
        Returns:
            Dictionary with state info
        """
        return {
            "current_state": self.current_state.value,
            "context": self.context,
            "error_message": self.error_message,
            "transition_count": len(self.transitions),
            "last_transition": self.transitions[-1] if self.transitions else None
        }
    
    def get_transition_history(self) -> list[Dict[str, Any]]:
        """
        Get transition history.
        
        Returns:
            List of transition records
        """
        return [
            {
                "from": t.from_state.value,
                "to": t.to_state.value,
                "trigger": t.trigger,
                "timestamp": t.timestamp.isoformat(),
                "metadata": t.metadata
            }
            for t in self.transitions
        ]