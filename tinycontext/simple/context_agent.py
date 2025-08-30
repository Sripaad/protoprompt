"""
ContextAgent - Simplified interface to TinyContext's multi-agent orchestration

This class provides a single entry point that automatically manages:
- Context engineering patterns (Write/Select/Compress/Isolate)  
- Agent creation and lifecycle
- Task routing and execution
- Optional observability integration

Implements 12-Factor Agent principles:
- Natural language to tool calls
- Own your prompts
- Context window management  
- Unified state management
- Small, focused agents
"""

import os
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .context_patterns import (
    ContextWriter, 
    ContextSelector, 
    ContextCompressor, 
    ContextIsolator
)

try:
    from ..manager.async_context_manager import AsyncTinyContextManager
    from ..agents.proto_factory import ProtoFactory
    from ..context.context_manager import ContextManager
    HAS_FULL_FRAMEWORK = True
except ImportError:
    HAS_FULL_FRAMEWORK = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class ContextAgent:
    """
    Simplified agent interface with automatic context engineering
    
    Example:
        ```python
        agent = ContextAgent()
        result = await agent.run("Analyze this data", data={"sales": [1,2,3]})
        ```
    """
    
    def __init__(self, 
                 name: str = "context_agent",
                 use_full_framework: bool = None,
                 enable_observability: bool = None,
                 storage_path: str = None):
        """
        Initialize ContextAgent with auto-configuration
        
        Args:
            name: Agent identifier
            use_full_framework: Use full TinyContext orchestration (auto-detected)
            enable_observability: Enable TensorZero observability (auto-detected) 
            storage_path: Path for persistent context storage
        """
        self.name = name
        self.logger = logging.getLogger(f"tinycontext.simple.{name}")
        
        # Auto-detect capabilities
        self.use_full_framework = use_full_framework if use_full_framework is not None else HAS_FULL_FRAMEWORK
        self.enable_observability = enable_observability if enable_observability is not None else self._detect_observability()
        
        # Initialize context engineering components
        self.context_writer = ContextWriter(storage_path)
        self.context_selector = ContextSelector()  
        self.context_compressor = ContextCompressor()
        self.context_isolator = ContextIsolator()
        
        # Full framework components (if available)
        self.manager = None
        self.factory = None
        self.context_manager = None
        
        # Simple client fallback (Groq/OpenAI)
        self.openai_client = None
        self.simple_mode_model = None
        
        # Task execution state
        self.conversation_history: List[Dict] = []
        self.context_memory: Dict[str, Any] = {}
        self.isolated_contexts: Dict[str, str] = {}
        
    async def initialize(self) -> None:
        """Initialize agent with auto-detected configuration"""
        self.logger.info(f"Initializing ContextAgent '{self.name}'")
        
        if self.use_full_framework:
            await self._initialize_full_framework()
        else:
            await self._initialize_simple_client()
            
        self.logger.info(f"ContextAgent initialized (full_framework={self.use_full_framework})")
    
    async def run(self, 
                 task: str,
                 data: Optional[Dict[str, Any]] = None,
                 context_strategy: str = "auto",
                 max_iterations: int = 5,
                 **kwargs) -> Dict[str, Any]:
        """
        Execute a task with automatic context engineering
        
        Args:
            task: Natural language description of the task
            data: Input data for the task  
            context_strategy: "auto", "compress", "isolate", or "select"
            max_iterations: Maximum execution iterations
            **kwargs: Additional parameters
            
        Returns:
            Dict containing result, metadata, and context info
        """
        if not self.manager and not self.openai_client:
            await self.initialize()
        
        # Apply context engineering strategy
        engineered_context = await self._apply_context_strategy(
            task, data, context_strategy
        )
        
        # Execute task
        if self.use_full_framework:
            result = await self._execute_with_framework(
                task, engineered_context, max_iterations, **kwargs
            )
        else:
            result = await self._execute_simple(
                task, engineered_context, max_iterations, **kwargs
            )
        
        # Store result in context memory
        await self.context_writer.write_memory(
            f"task_result_{len(self.conversation_history)}", 
            result,
            metadata={"task": task, "strategy": context_strategy}
        )
        
        return result
    
    async def add_context(self, 
                         key: str, 
                         content: str,
                         tags: Optional[List[str]] = None,
                         persistent: bool = True) -> None:
        """Add context information for future task execution"""
        # Add to selector for retrieval
        await self.context_selector.add_context(key, content, tags)
        
        # Optionally persist
        if persistent:
            await self.context_writer.write_memory(key, content, {"tags": tags})
            
        self.logger.debug(f"Added context '{key}' with tags {tags}")
    
    async def get_conversation_history(self, compressed: bool = False) -> List[Dict]:
        """Get conversation history, optionally compressed"""
        if not compressed or len(self.conversation_history) <= 5:
            return self.conversation_history
            
        compressed_result = await self.context_compressor.compress_conversation(
            self.conversation_history
        )
        return compressed_result["messages"]
    
    async def create_isolated_context(self, 
                                    context_name: str,
                                    schema: Dict[str, Any]) -> str:
        """Create isolated context for specialized task handling"""
        context_id = await self.context_isolator.create_isolated_context(
            context_name, schema
        )
        self.isolated_contexts[context_name] = context_id
        return context_id
    
    async def _apply_context_strategy(self, 
                                    task: str,
                                    data: Optional[Dict], 
                                    strategy: str) -> Dict[str, Any]:
        """Apply context engineering strategy"""
        engineered_context = {
            "task": task,
            "data": data or {},
            "strategy": strategy,
            "relevant_context": [],
            "compressed_history": None,
            "isolated_data": {}
        }
        
        if strategy in ["auto", "select"]:
            # Select relevant context
            relevant = await self.context_selector.select_relevant(task, max_contexts=3)
            engineered_context["relevant_context"] = relevant
        
        if strategy in ["auto", "compress"] and len(self.conversation_history) > 3:
            # Compress conversation history  
            compressed = await self.context_compressor.compress_conversation(
                self.conversation_history
            )
            engineered_context["compressed_history"] = compressed
        
        if strategy in ["auto", "isolate"]:
            # Create task-specific isolated context
            context_id = f"task_{len(self.conversation_history)}"
            schema = {"task": {"type": str}, "data": {"type": dict}, "result": {"type": dict}}
            await self.context_isolator.create_isolated_context(context_id, schema)
            await self.context_isolator.write_to_context(context_id, "task", task)
            await self.context_isolator.write_to_context(context_id, "data", data or {})
            engineered_context["isolated_data"]["context_id"] = context_id
        
        return engineered_context
    
    async def _initialize_full_framework(self) -> None:
        """Initialize with full TinyContext framework"""
        try:
            self.manager = AsyncTinyContextManager()
            await self.manager.initialize()
            
            self.factory = ProtoFactory()
            self.context_manager = ContextManager()
            
            self.logger.info("Full framework initialized successfully")
        except Exception as e:
            self.logger.warning(f"Full framework initialization failed: {e}")
            self.use_full_framework = False
            await self._initialize_simple_client()
    
    async def _initialize_simple_client(self) -> None:
        """Initialize with simple client fallback (supports Groq)"""
        if not HAS_OPENAI:
            raise ImportError(
                "OpenAI package required for simple mode. Install with: pip install openai"
            )
        
        # Try Groq first, fallback to OpenAI
        groq_api_key = os.getenv("GROQ_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if groq_api_key:
            self.openai_client = openai.AsyncOpenAI(
                api_key=groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.simple_mode_model = "llama3-groq-70b-8192-tool-use-preview"
            self.logger.info("Simple Groq client initialized")
        elif openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
            self.simple_mode_model = "gpt-4o-mini"
            self.logger.info("Simple OpenAI client initialized")
        else:
            raise ValueError(
                "Either GROQ_API_KEY or OPENAI_API_KEY environment variable required. "
                "Set one in your .env file or environment."
            )
    
    async def _execute_with_framework(self, 
                                    task: str,
                                    context: Dict[str, Any],
                                    max_iterations: int,
                                    **kwargs) -> Dict[str, Any]:
        """Execute task using full TinyContext framework"""
        try:
            # AsyncTinyContextManager.run() doesn't accept max_iterations or most kwargs
            # Filter kwargs to only include what the method accepts
            filtered_kwargs = {}
            if 'trace_id' in kwargs:
                filtered_kwargs['trace_id'] = kwargs['trace_id']
            
            result = await self.manager.run(
                task=task,
                input_data=context["data"],
                **filtered_kwargs
            )
            
            # Debug what we actually get back
            self.logger.debug(f"Framework result: {result}")
            self.logger.debug(f"Framework result type: {type(result)}")
            
            # Handle the actual return format from AsyncTinyContextManager
            success = result.get("success", False)
            output = result.get("output", "")
            
            self.conversation_history.append({
                "role": "user",
                "content": task,
                "data": context["data"]
            })
            
            self.conversation_history.append({
                "role": "assistant", 
                "content": output if success else f"Error: {result.get('error', 'Unknown error')}",
                "metadata": result
            })
            
            if success:
                return {
                    "success": True,
                    "output": output,
                    "agents_used": result.get("agents", []),
                    "trace_id": result.get("trace_id"),
                    "duration_ms": result.get("duration_ms", 0),
                    "context_strategy": context["strategy"],
                    "framework": "full"
                }
            else:
                # Framework returned an error  
                return {
                    "success": False,
                    "error": result.get("error", "Unknown framework error"),
                    "trace_id": result.get("trace_id"),
                    "framework": "full"
                }
            
        except Exception as e:
            self.logger.error(f"Framework execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "framework": "full"
            }
    
    async def _execute_simple(self, 
                            task: str,
                            context: Dict[str, Any], 
                            max_iterations: int,
                            **kwargs) -> Dict[str, Any]:
        """Execute task using simple OpenAI client"""
        try:
            # Build prompt with context engineering
            prompt = await self._build_context_prompt(task, context)
            
            # Use streaming for maximum speed (76% faster with Groq)
            stream = await self.openai_client.chat.completions.create(
                model=kwargs.get("model", self.simple_mode_model or "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant that analyzes tasks and provides detailed responses."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000),
                stream=True  # Enable streaming for speed
            )
            
            # Collect streamed response
            output_chunks = []
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    output_chunks.append(chunk.choices[0].delta.content)
            
            output = ''.join(output_chunks)
            
            # Create response-like object for compatibility
            class StreamedResponse:
                def __init__(self, content, model):
                    self.choices = [type('Choice', (), {
                        'message': type('Message', (), {'content': content})()
                    })()]
                    self.usage = type('Usage', (), {'total_tokens': len(content.split())})()  # Rough estimate
            
            response = StreamedResponse(output, kwargs.get("model", self.simple_mode_model))
            
            output = response.choices[0].message.content
            
            self.conversation_history.append({
                "role": "user",
                "content": task,
                "data": context["data"]
            })
            
            self.conversation_history.append({
                "role": "assistant",
                "content": output
            })
            
            return {
                "success": True,
                "output": output,
                "context_strategy": context["strategy"],
                "framework": "simple",
                "tokens_used": response.usage.total_tokens if response.usage else None
            }
            
        except Exception as e:
            self.logger.error(f"Simple execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "framework": "simple"
            }
    
    async def _build_context_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """Build prompt with engineered context"""
        prompt_parts = [f"Task: {task}"]
        
        # Add input data
        if context["data"]:
            prompt_parts.append(f"Input Data: {context['data']}")
        
        # Add relevant context
        if context["relevant_context"]:
            prompt_parts.append("Relevant Context:")
            for ctx in context["relevant_context"]:
                prompt_parts.append(f"- {ctx['content']}")
        
        # Add compressed history
        if context["compressed_history"] and context["compressed_history"]["summary"]:
            prompt_parts.append(f"Previous Context: {context['compressed_history']['summary']}")
        
        # Add isolated context data
        if context["isolated_data"]:
            prompt_parts.append(f"Context Strategy: {context['strategy']}")
        
        return "\n\n".join(prompt_parts)
    
    def _detect_observability(self) -> bool:
        """Auto-detect if observability should be enabled"""
        return os.getenv("ENABLE_OBSERVABILITY", "false").lower() == "true"
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Cleanup if needed
        pass