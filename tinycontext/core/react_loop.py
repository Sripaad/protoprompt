"""
ReAct loop implementation for TinyPerson agents with async support.
"""

import asyncio
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from ..agents.loader import TinyPerson


@dataclass
class ReActStep:
    """Represents a single ReAct step."""
    reasoning: str
    action: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = None


class AsyncReActLoop:
    """
    Async implementation of ReAct (Reason + Act) pattern for agent execution.
    
    Supports concurrent reasoning and action generation.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the async ReAct loop.
        
        Args:
            llm_client: Async LLM client for inference (AsyncTensorZeroClient)
        """
        self.llm_client = llm_client
        self.current_agents: Dict[str, TinyPerson] = {}
        self.contexts: Dict[str, Dict[str, Any]] = {}
    
    async def reason(self, agent: TinyPerson, input_text: str, context: Dict[str, Any] = None, episode_id: Optional[str] = None) -> str:
        """
        Async reasoning phase - analyze input and determine approach.
        
        Args:
            agent: The TinyPerson agent doing the reasoning
            input_text: Input to reason about
            context: Additional context
            
        Returns:
            Reasoning output as string
        """
        self.current_agents[agent.name] = agent
        self.contexts[agent.name] = context or {}
        
        # Build reasoning prompt
        prompt = self._build_reasoning_prompt(agent, input_text)
        
        # If no LLM client, return template response
        if not self.llm_client:
            return f"[{agent.role}] Analyzing: {input_text}"
        
        # Async LLM call for reasoning
        try:
            response = await self.llm_client.call(
                function_name="tiny_reasoning",
                episode_id=episode_id,
                input_text=prompt,
                agent_role=agent.role,
                system_prompt=agent.prompts.system
            )
            return response
        except Exception as e:
            return f"Reasoning error: {e}"
    
    async def act(self, agent: TinyPerson, reasoning: str, episode_id: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        Async action phase - determine and format action based on reasoning.
        
        Args:
            agent: The TinyPerson agent taking action
            reasoning: The reasoning output
            
        Returns:
            Tuple of (action, optional_handoff_agent)
        """
        # Build action prompt
        prompt = self._build_action_prompt(agent, reasoning)
        
        # If no LLM client, return template response
        if not self.llm_client:
            return f"[{agent.role}] Action based on reasoning", None
        
        # Async LLM call for action
        try:
            response = await self.llm_client.call(
                function_name="tiny_action",
                episode_id=episode_id,
                reasoning=reasoning,
                agent_role=agent.role,
                system_prompt=agent.prompts.system
            )
            
            # Parse for handoff directive
            handoff_agent = self._extract_handoff(response)
            
            return response, handoff_agent
        except Exception as e:
            return f"Action error: {e}", None
    
    async def execute_step(self, agent: TinyPerson, input_text: str, context: Dict[str, Any] = None, episode_id: Optional[str] = None) -> ReActStep:
        """
        Execute a complete async ReAct step.
        
        Args:
            agent: The TinyPerson agent
            input_text: Input to process
            context: Additional context
            
        Returns:
            ReActStep with reasoning and action
        """
        # Async reasoning phase
        reasoning = await self.reason(agent, input_text, context, episode_id)
        
        # Async action phase
        action, handoff = await self.act(agent, reasoning, episode_id)
        
        # Create step record
        step = ReActStep(
            reasoning=reasoning,
            action=action,
            confidence=0.8,  # Could be enhanced with confidence scoring
            metadata={
                "agent": agent.name,
                "role": agent.role,
                "handoff": handoff
            }
        )
        
        return step
    
    async def execute_concurrent_steps(
        self, 
        agent_tasks: List[Tuple[TinyPerson, str, Dict[str, Any]]]
    ) -> List[ReActStep]:
        """
        Execute multiple ReAct steps concurrently.
        
        Args:
            agent_tasks: List of (agent, input_text, context) tuples
            
        Returns:
            List of ReActStep results in the same order
        """
        # Create tasks for all agent steps
        tasks = [
            self.execute_step(agent, input_text, context)
            for agent, input_text, context in agent_tasks
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        return results
    
    async def reason_concurrent(
        self,
        agent_inputs: List[Tuple[TinyPerson, str, Dict[str, Any]]]
    ) -> List[str]:
        """
        Perform reasoning for multiple agents concurrently.
        
        Args:
            agent_inputs: List of (agent, input_text, context) tuples
            
        Returns:
            List of reasoning outputs
        """
        tasks = [
            self.reason(agent, input_text, context)
            for agent, input_text, context in agent_inputs
        ]
        
        results = await asyncio.gather(*tasks)
        return results
    
    def _build_reasoning_prompt(self, agent: TinyPerson, input_text: str) -> str:
        """
        Build the reasoning prompt for an agent.
        
        Args:
            agent: The agent
            input_text: Input to reason about
            
        Returns:
            Formatted prompt
        """
        # Use agent's reasoning template if available
        if agent.prompts.reasoning_template:
            return agent.prompts.reasoning_template.format(input=input_text)
        
        context = self.contexts.get(agent.name, {})
        
        # Default reasoning prompt
        prompt = f"""
You are {agent.name}, a {agent.role}.
{agent.persona}

Input: {input_text}

Context: {context}

System Prompt: {agent.prompts.system}

Please reason through this step-by-step, considering your role and expertise.
What approach should you take?
"""
        return prompt.strip()
    
    def _build_action_prompt(self, agent: TinyPerson, reasoning: str) -> str:
        """
        Build the action prompt for an agent.
        
        Args:
            agent: The agent
            reasoning: The reasoning output
            
        Returns:
            Formatted prompt
        """
        # Use agent's action template if available
        if agent.prompts.action_template:
            try:
                # Provide multiple variable names for template flexibility
                template_vars = {
                    'reasoning': reasoning,
                    'action': "[determine action]",
                    'insights': reasoning,  # Map insights to reasoning
                    'analysis': reasoning,  # Map analysis to reasoning  
                    'output': reasoning,    # Map output to reasoning
                    'input': reasoning      # Map input to reasoning
                }
                return agent.prompts.action_template.format(**template_vars)
            except KeyError as e:
                # If template has unexpected variables, fall back to default
                print(f"Warning: Action template contains unexpected variable {e}, using default prompt")
                pass
        
        # Default action prompt
        prompt = f"""
Based on your reasoning: {reasoning}

What specific action should you take?
If another agent would be better suited, indicate "HANDOFF: [agent_role]"

Provide a clear, actionable response.
"""
        return prompt.strip()
    
    def _extract_handoff(self, action: str) -> Optional[str]:
        """
        Extract handoff directive from action.
        
        Args:
            action: Action string
            
        Returns:
            Agent role to hand off to, or None
        """
        if "HANDOFF:" in action:
            parts = action.split("HANDOFF:")
            if len(parts) > 1:
                handoff = parts[1].strip().split()[0]
                return handoff.strip("[]")
        return None


class ReActLoop:
    """
    Synchronous wrapper for AsyncReActLoop.
    
    For backward compatibility with sync code.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the sync ReAct loop.
        
        Args:
            llm_client: LLM client for inference
        """
        self.async_loop = AsyncReActLoop(llm_client)
        self._event_loop = None
    
    def _get_loop(self):
        """Get or create event loop."""
        if self._event_loop is None:
            try:
                self._event_loop = asyncio.get_running_loop()
            except RuntimeError:
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
        return self._event_loop
    
    def reason(self, agent: TinyPerson, input_text: str, context: Dict[str, Any] = None) -> str:
        """Sync wrapper for reasoning."""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_loop.reason(agent, input_text, context)
        )
    
    def act(self, agent: TinyPerson, reasoning: str) -> Tuple[str, Optional[str]]:
        """Sync wrapper for action."""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_loop.act(agent, reasoning)
        )
    
    def execute_step(self, agent: TinyPerson, input_text: str, context: Dict[str, Any] = None) -> ReActStep:
        """Sync wrapper for execute_step."""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_loop.execute_step(agent, input_text, context)
        )