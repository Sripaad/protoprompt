"""
Tests for TinyWorld FSM.
"""

import pytest
from tinycontext.core.tiny_world import TinyWorld, AgentState


def test_initial_state():
    """Test FSM starts in IDLE state."""
    world = TinyWorld()
    assert world.current_state == AgentState.IDLE
    assert world.error_message is None
    assert len(world.transitions) == 0


def test_valid_transitions():
    """Test valid state transitions."""
    world = TinyWorld()
    
    # IDLE -> THINKING
    assert world.start_thinking("test input")
    assert world.current_state == AgentState.THINKING
    assert world.context["input"] == "test input"
    
    # THINKING -> ACTING
    assert world.complete_thinking("test reasoning")
    assert world.current_state == AgentState.ACTING
    assert world.context["reasoning"] == "test reasoning"
    
    # ACTING -> IDLE
    assert world.complete_action("test action")
    assert world.current_state == AgentState.IDLE
    assert world.context["action"] == "test action"


def test_handoff_transition():
    """Test handoff state transition."""
    world = TinyWorld()
    
    # Setup to ACTING state
    world.start_thinking("input")
    world.complete_thinking("reasoning")
    assert world.current_state == AgentState.ACTING
    
    # ACTING -> HANDING_OFF
    assert world.complete_action("action", handoff_to="planner")
    assert world.current_state == AgentState.HANDING_OFF
    assert world.context["handoff_to"] == "planner"
    
    # HANDING_OFF -> IDLE
    assert world.complete_handoff()
    assert world.current_state == AgentState.IDLE


def test_error_handling():
    """Test error state transitions."""
    world = TinyWorld()
    
    # Enter error from any state
    assert world.enter_error("test error")
    assert world.current_state == AgentState.ERROR
    assert world.error_message == "test error"
    
    # Recover from error
    assert world.recover_from_error()
    assert world.current_state == AgentState.IDLE
    assert world.error_message is None


def test_invalid_transitions():
    """Test invalid state transitions are rejected."""
    world = TinyWorld()
    
    # Can't go from IDLE to ACTING directly
    assert not world.complete_action("action")
    assert world.current_state == AgentState.IDLE
    
    # Can't go from THINKING to IDLE directly
    world.start_thinking("input")
    assert not world.complete_handoff()
    assert world.current_state == AgentState.THINKING


def test_transition_history():
    """Test transition history tracking."""
    world = TinyWorld()
    
    world.start_thinking("input")
    world.complete_thinking("reasoning")
    world.complete_action("action")
    
    history = world.get_transition_history()
    assert len(history) == 3
    
    # Check transition sequence
    assert history[0]["from"] == "idle"
    assert history[0]["to"] == "thinking"
    assert history[1]["from"] == "thinking"
    assert history[1]["to"] == "acting"
    assert history[2]["from"] == "acting"
    assert history[2]["to"] == "idle"


def test_reset():
    """Test FSM reset functionality."""
    world = TinyWorld()
    
    # Make some transitions
    world.start_thinking("input")
    world.complete_thinking("reasoning")
    
    # Reset
    world.reset()
    
    assert world.current_state == AgentState.IDLE
    assert len(world.transitions) == 0
    assert len(world.context) == 0
    assert world.error_message is None


def test_callbacks():
    """Test state enter/exit callbacks."""
    world = TinyWorld()
    callback_log = []
    
    def on_enter_thinking(w):
        callback_log.append("enter_thinking")
    
    def on_exit_thinking(w):
        callback_log.append("exit_thinking")
    
    world.register_on_enter(AgentState.THINKING, on_enter_thinking)
    world.register_on_exit(AgentState.THINKING, on_exit_thinking)
    
    world.start_thinking("input")
    world.complete_thinking("reasoning")
    
    assert "enter_thinking" in callback_log
    assert "exit_thinking" in callback_log