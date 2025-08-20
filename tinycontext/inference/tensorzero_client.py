"""
TensorZero client for LLM inference with async support.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

try:
    from tensorzero import AsyncTensorZeroGateway, TensorZeroGateway
    TENSORZERO_AVAILABLE = True
except ImportError:
    TENSORZERO_AVAILABLE = False
    print("Warning: TensorZero not available. Using fallback implementation.")

# Load environment variables
load_dotenv()


class AsyncTensorZeroClient:
    """
    Async client for TensorZero LLM inference.
    
    Supports both real TensorZero API and fallback simulation.
    """
    
    def __init__(self, config_path: Optional[str] = None, use_embedded: bool = True):
        """
        Initialize async TensorZero client.
        
        Args:
            config_path: Path to tensorzero.toml configuration
            use_embedded: Use embedded gateway (True) or HTTP gateway (False)
        """
        self.config_path = config_path or "tensorzero.toml"
        self.use_embedded = use_embedded
        self.gateway: Optional[AsyncTensorZeroGateway] = None
        self.initialized = False
        
        # Default model (fallback to gpt-4o-mini if gpt-5 not available)
        self.default_model = os.getenv("TENSORZERO_MODEL", "openai::gpt-4o-mini")
        
        # Function to model mapping
        self.function_models = {
            "tiny_reasoning": self.default_model,
            "tiny_action": self.default_model,
            "agent_selection": self.default_model
        }
    
    async def initialize(self) -> None:
        """
        Initialize the TensorZero gateway.
        Must be called before making inference requests.
        """
        if self.initialized:
            return
        
        if TENSORZERO_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                if self.use_embedded:
                    # Use embedded gateway (no separate service needed)
                    # Check if ClickHouse is available for observability
                    clickhouse_url = os.getenv("TENSORZERO_CLICKHOUSE_URL", 
                                               "http://chuser:chpassword@localhost:8123/tensorzero")
                    self.gateway = await AsyncTensorZeroGateway.build_embedded(
                        config_file=self.config_path,
                        clickhouse_url=clickhouse_url if os.getenv("ENABLE_OBSERVABILITY", "false").lower() == "true" else None
                    )
                else:
                    # Use HTTP gateway (requires running TensorZero service)
                    gateway_url = os.getenv("TENSORZERO_GATEWAY_URL", "http://localhost:3000")
                    self.gateway = await AsyncTensorZeroGateway.build_http(
                        gateway_url=gateway_url
                    )
                
                self.initialized = True
                print(f"✅ TensorZero initialized with {self.default_model}")
            except Exception as e:
                print(f"⚠️ TensorZero initialization failed: {e}")
                print("   Falling back to simulation mode")
                self.gateway = None
                self.initialized = True
        else:
            if not TENSORZERO_AVAILABLE:
                print("⚠️ TensorZero package not available")
            if not os.getenv("OPENAI_API_KEY"):
                print("⚠️ OPENAI_API_KEY not set")
            print("   Using simulation mode")
            self.initialized = True
    
    async def call(self, function_name: str, **kwargs) -> str:
        """
        Call a TensorZero function asynchronously.
        
        Args:
            function_name: Name of the function to call
            **kwargs: Function arguments
            
        Returns:
            LLM response string
        """
        if not self.initialized:
            await self.initialize()
        
        # Use real TensorZero if available
        if self.gateway:
            try:
                result = await self._call_tensorzero(function_name, **kwargs)
                print(f"✓ TensorZero call successful for {function_name}")
                return result
            except Exception as e:
                print(f"⚠️ TensorZero call failed for {function_name}: {e}")
                import traceback
                traceback.print_exc()
                # Fall through to simulation
        
        # Fallback to simulation
        return await self._simulate_response(function_name, **kwargs)
    
    async def call_concurrent(self, calls: List[Dict[str, Any]]) -> List[str]:
        """
        Make multiple concurrent LLM calls.
        
        Args:
            calls: List of call specifications, each with 'function' and 'kwargs'
            
        Returns:
            List of responses in the same order as calls
        """
        if not self.initialized:
            await self.initialize()
        
        # Create tasks for all calls
        tasks = [
            self.call(call_spec['function'], **call_spec.get('kwargs', {}))
            for call_spec in calls
        ]
        
        # Execute all tasks concurrently
        responses = await asyncio.gather(*tasks)
        return responses
    
    async def _call_tensorzero(self, function_name: str, **kwargs) -> str:
        """
        Make actual TensorZero API call.
        
        Args:
            function_name: Function to call
            **kwargs: Function arguments
            
        Returns:
            LLM response
        """
        model = self.function_models.get(function_name, self.default_model)
        
        # Build prompt based on function
        if function_name == "tiny_reasoning":
            prompt = self._build_reasoning_prompt(**kwargs)
        elif function_name == "tiny_action":
            prompt = self._build_action_prompt(**kwargs)
        elif function_name == "agent_selection":
            prompt = self._build_selection_prompt(**kwargs)
        else:
            prompt = kwargs.get("prompt", "")
        
        # Build input based on function requirements
        # TensorZero only accepts "user" and "assistant" roles
        # Combine system prompt with user message if provided
        system_prompt = kwargs.get("system_prompt", "")
        
        if function_name == "tiny_reasoning" and system_prompt:
            # Prepend system context to the user message
            full_prompt = f"{system_prompt}\n\n{prompt}"
            input_data = {
                "messages": [
                    {
                        "role": "user", 
                        "content": full_prompt
                    }
                ]
            }
        else:
            input_data = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        
        # Make inference request using function_name
        response = await self.gateway.inference(
            function_name=function_name,
            input=input_data
        )
        
        # Extract text from response
        # TensorZero returns a ChatModelInferenceResponse with content field
        if hasattr(response, 'content'):
            # Content is a list of content blocks
            if response.content and len(response.content) > 0:
                content_block = response.content[0]
                # Extract text from the content block
                if hasattr(content_block, 'text'):
                    return content_block.text
                elif isinstance(content_block, dict) and 'text' in content_block:
                    return content_block['text']
                else:
                    return str(content_block)
            return ""
        elif hasattr(response, 'text'):
            return response.text
        elif isinstance(response, dict):
            # Handle dict response
            if 'content' in response and response['content']:
                content = response['content'][0] if isinstance(response['content'], list) else response['content']
                return content.get('text', str(content))
            return response.get('text', str(response))
        else:
            return str(response)
    
    def _build_reasoning_prompt(self, **kwargs) -> str:
        """Build reasoning prompt."""
        input_text = kwargs.get("input_text", "")
        agent_role = kwargs.get("agent_role", "assistant")
        
        return f"""You are a TinyPerson agent with the role: {agent_role}

Input: {input_text}

Please reason through this step-by-step:
1. Understand the core requirement
2. Consider your role and expertise
3. Identify the best approach
4. Determine appropriate actions

Provide clear, logical reasoning."""
    
    def _build_action_prompt(self, **kwargs) -> str:
        """Build action prompt."""
        reasoning = kwargs.get("reasoning", "")
        
        return f"""Based on your reasoning:
{reasoning}

What specific action should you take?
If another agent would be better suited, indicate "HANDOFF: [agent_role]"

Provide a clear, actionable response."""
    
    def _build_selection_prompt(self, **kwargs) -> str:
        """Build agent selection prompt."""
        task = kwargs.get("task", "")
        agents = kwargs.get("agents", [])
        
        agent_list = ", ".join(agents) if agents else "strategist, planner, analyzer"
        
        return f"""Task: {task}
Available agents: {agent_list}

Which agent is best suited for this task? Return only the agent role."""
    
    async def _simulate_response(self, function_name: str, **kwargs) -> str:
        """
        Simulate LLM response for fallback.
        
        Args:
            function_name: Function being called
            **kwargs: Arguments
            
        Returns:
            Simulated response
        """
        # Add slight delay to simulate API call
        await asyncio.sleep(0.1)
        
        if function_name == "tiny_reasoning":
            input_text = kwargs.get("input_text", "")
            agent_role = kwargs.get("agent_role", "agent")
            
            return f"""As a {agent_role}, I'm analyzing: {input_text}

Step-by-step reasoning:
1. The task requires {agent_role} expertise
2. I should apply my specialized knowledge
3. The best approach involves systematic analysis
4. I'll provide actionable recommendations

This task aligns with my {agent_role} capabilities."""
        
        elif function_name == "tiny_action":
            reasoning = kwargs.get("reasoning", "")
            
            if "strategist" in reasoning.lower():
                return "I'll create a comprehensive strategic framework to address this challenge."
            elif "analyzer" in reasoning.lower():
                return "I'll perform detailed data analysis to uncover patterns and insights."
            elif "planner" in reasoning.lower():
                return "I'll develop an executable plan with clear milestones."
            else:
                return "I'll proceed with the appropriate action based on the analysis."
        
        elif function_name == "agent_selection":
            task = kwargs.get("task", "").lower()
            
            if "strategy" in task or "strategic" in task:
                return "strategist"
            elif "analyze" in task or "data" in task:
                return "analyzer"
            elif "plan" in task or "execute" in task:
                return "planner"
            else:
                return "assistant"
        
        return "Completed processing."
    
    async def close(self) -> None:
        """
        Close the TensorZero gateway connection.
        """
        if self.gateway:
            # TensorZero gateway cleanup if needed
            self.gateway = None
        self.initialized = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class TensorZeroClient:
    """
    Synchronous wrapper for AsyncTensorZeroClient.
    
    For backward compatibility with sync code.
    """
    
    def __init__(self, config_path: Optional[str] = None, use_embedded: bool = True):
        """Initialize sync client."""
        self.async_client = AsyncTensorZeroClient(config_path, use_embedded)
        self._loop = None
    
    def _get_loop(self):
        """Get or create event loop."""
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop
    
    def call(self, function_name: str, **kwargs) -> str:
        """
        Synchronous call wrapper.
        
        Args:
            function_name: Function to call
            **kwargs: Arguments
            
        Returns:
            Response string
        """
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_client.call(function_name, **kwargs)
        )
    
    def close(self) -> None:
        """Close the client."""
        if self._loop:
            self._loop.run_until_complete(self.async_client.close())