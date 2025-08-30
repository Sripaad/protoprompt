"""
TinyContext Simple API - Minimal entry point for context engineering

This module provides a simplified interface to TinyContext's powerful
multi-agent orchestration capabilities, focusing on context engineering
patterns from the research:

- Write Context: Save information outside context window
- Select Context: Retrieve relevant information for tasks  
- Compress Context: Summarize long interaction trajectories
- Isolate Context: Split context across specialized agents

Examples:
    ```python
    # Quick start (zero config)
    from tinycontext.simple import quick_start
    agent = quick_start()
    result = await agent.run("Analyze this data", data={"sales": [1,2,3]})
    
    # Or manual setup  
    from tinycontext.simple import ContextAgent
    agent = ContextAgent()
    await agent.initialize()
    result = await agent.run("Hello world!")
    
    # One-line usage
    from tinycontext.simple import run_quick_task
    result = await run_quick_task("Summarize this text", data={"text": "..."})
    ```
"""

from .context_agent import ContextAgent
from .context_patterns import (
    ContextWriter,
    ContextSelector, 
    ContextCompressor,
    ContextIsolator
)
from .quick_start import quick_start, setup_environment, run_quick_task

__all__ = [
    "ContextAgent",
    "ContextWriter",
    "ContextSelector", 
    "ContextCompressor",
    "ContextIsolator",
    "quick_start",
    "setup_environment", 
    "run_quick_task"
]