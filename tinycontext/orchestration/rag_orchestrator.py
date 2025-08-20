"""
RAG Orchestrator for managing multi-agent information retrieval workflows.

Coordinates TinyPerson agents working together in a RAG world to answer queries.
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

from ..core.rag_world import AsyncRAGWorld, RAGState, RAGAction
from ..core.react_loop import AsyncReActLoop
from ..agents.rag_agents import RAGAgentFactory, RAGContext
from ..agents.loader import TinyPerson
from ..inference.tensorzero_client import AsyncTensorZeroClient
from ..manager.async_context_manager import AsyncTinyContextManager


class RAGOrchestrator:
    """
    Orchestrates multi-agent RAG workflows using TinyPerson agents.
    """
    
    def __init__(
        self,
        llm_client: Optional[AsyncTensorZeroClient] = None,
        context_manager: Optional[AsyncTinyContextManager] = None
    ):
        """
        Initialize RAG orchestrator.
        
        Args:
            llm_client: LLM client for agent inference
            context_manager: Context manager for agent coordination
        """
        self.llm_client = llm_client
        self.context_manager = context_manager or AsyncTinyContextManager(llm_client=llm_client)
        self.react_loop = AsyncReActLoop(llm_client=llm_client)
        
        # Create RAG world
        self.world = AsyncRAGWorld(world_id="rag_world")
        
        # Load RAG agents
        self.agents = RAGAgentFactory.create_rag_team()
        self.current_agent: Optional[TinyPerson] = None
        
        # Execution tracking
        self.execution_id = None
        self.start_time = None
        self.handoff_count = 0
    
    async def initialize(self) -> None:
        """Initialize the orchestrator and its components."""
        if self.llm_client and not self.llm_client.initialized:
            await self.llm_client.initialize()
        
        await self.context_manager.initialize()
        
        # Store agents for use (context manager already handles TinyPerson internally)
        # No need to register, they'll be used directly in the workflow
    
    async def answer_query(
        self,
        query: str,
        max_iterations: int = 10,
        verbose: bool = True,
        episode_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a query using multi-agent RAG workflow.
        
        Args:
            query: The question to answer
            max_iterations: Maximum reasoning iterations
            verbose: Whether to print progress
            episode_id: Optional episode ID for TensorZero tracking
            
        Returns:
            Dictionary with answer and execution details
        """
        # Initialize execution
        self.execution_id = f"rag_{datetime.now().timestamp()}"
        self.start_time = datetime.now()
        self.handoff_count = 0
        
        # Generate episode ID if not provided (must be UUID v7 for TensorZero)
        if not episode_id:
            import uuid_utils
            episode_id = str(uuid_utils.uuid7())
        self.episode_id = episode_id
        
        # Initialize RAG context
        self.world.initialize_rag_context(query, max_iterations)
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"🔍 RAG Query: {query}")
            print(f"{'='*60}\n")
        
        # Start with router agent to determine approach
        self.current_agent = self.agents["router"]
        await self.world.assign_agent(self.current_agent.name)
        
        # Main RAG loop
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            if verbose:
                print(f"\n📍 Iteration {iteration} | Agent: {self.current_agent.name}")
            
            # Determine next action based on current agent and state
            next_action = await self._determine_next_action()
            
            if verbose:
                print(f"   Action: {next_action}")
            
            # Execute the action
            result = await self._execute_action(next_action)
            
            # Check if we should continue
            if not await self.world.should_continue_gathering():
                if verbose:
                    print("\n✅ Sufficient information gathered")
                break
            
            # Handle agent handoffs
            handoff_agent = await self._check_for_handoff(result)
            if handoff_agent:
                await self._handoff_to_agent(handoff_agent)
                if verbose:
                    print(f"   🤝 Handing off to: {handoff_agent}")
        
        # Synthesize final answer
        if verbose:
            print("\n📝 Synthesizing final answer...")
        
        self.current_agent = self.agents["answerer"]
        await self.world.assign_agent(self.current_agent.name)
        final_answer = await self.world.execute_synthesize()
        
        # Prepare result
        execution_time = (datetime.now() - self.start_time).total_seconds()
        
        result = {
            "answer": final_answer,
            "execution_id": self.execution_id,
            "query": query,
            "execution_time": execution_time,
            "iterations": iteration,
            "handoffs": self.handoff_count,
            "actions": self.world.get_action_summary(),
            "confidence": self.world.rag_context.confidence_score if self.world.rag_context else 0,
            "message_history": self.world.get_message_history()
        }
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"✨ Query answered in {execution_time:.2f}s")
            print(f"   Iterations: {iteration}")
            print(f"   Handoffs: {self.handoff_count}")
            print(f"   Confidence: {result['confidence']:.0%}")
            print(f"{'='*60}\n")
        
        return result
    
    async def _determine_next_action(self) -> str:
        """
        Determine the next action based on current agent and world state.
        
        Returns:
            Action type to execute
        """
        agent_name = self.current_agent.name
        
        # Router determines initial approach
        if agent_name == "router":
            return "route"
        
        # Searcher performs searches
        elif agent_name == "searcher":
            if self.world.search_count == 0:
                return "initial_search"
            else:
                return "refined_search"
        
        # Loader extracts content
        elif agent_name == "loader":
            return "load_content"
        
        # Thinker reasons about information
        elif agent_name == "thinker":
            return "think"
        
        # Fact checker verifies information
        elif agent_name == "fact_checker":
            return "verify"
        
        # Answerer synthesizes
        elif agent_name == "answerer":
            return "synthesize"
        
        return "think"  # Default to thinking
    
    async def _execute_action(self, action_type: str) -> Dict[str, Any]:
        """
        Execute a specific action in the RAG workflow.
        
        Args:
            action_type: Type of action to execute
            
        Returns:
            Action result
        """
        result = {}
        
        if action_type == "route":
            # Determine which agent should handle the query
            step = await self.react_loop.execute_step(
                self.current_agent,
                f"Route this query: {self.world.rag_context.original_query}",
                {"iteration": self.world.rag_context.iteration_count},
                episode_id=self.episode_id
            )
            
            # Determine next agent based on reasoning
            if "search" in step.reasoning.lower():
                result["next_agent"] = "searcher"
            elif "think" in step.reasoning.lower() or "complex" in step.reasoning.lower():
                result["next_agent"] = "thinker"
            else:
                result["next_agent"] = "searcher"
            
            result["reasoning"] = step.reasoning
        
        elif action_type in ["initial_search", "refined_search"]:
            # Execute search
            query = self.world.rag_context.original_query
            if action_type == "refined_search" and self.world.rag_context.search_history:
                # Refine based on previous searches
                query = f"{query} (refined)"
            
            step = await self.react_loop.execute_step(
                self.current_agent,
                f"Search for: {query}",
                {"search_type": "web", "iteration": self.world.rag_context.iteration_count},
                episode_id=self.episode_id
            )
            
            # Execute actual search in world
            search_results = await self.world.execute_search(query)
            
            result["search_results"] = search_results
            result["query"] = query
            result["next_agent"] = "loader" if search_results else "thinker"
        
        elif action_type == "load_content":
            # Load content from search results
            if self.world.rag_context and self.world.rag_context.search_history:
                last_search = self.world.rag_context.search_history[-1]
                sources = last_search.get("results", [])[:2]  # Load top 2 results
                
                for source in sources:
                    content = await self.world.execute_load(source)
                    result[f"loaded_{source[:20]}"] = content[:200]
            
            result["next_agent"] = "thinker"
        
        elif action_type == "think":
            # Reason about gathered information
            context = self.world.rag_context.get_accumulated_knowledge() if self.world.rag_context else ""
            
            step = await self.react_loop.execute_step(
                self.current_agent,
                f"Analyze information and plan next steps: {context[:500]}",
                {"iteration": self.world.rag_context.iteration_count},
                episode_id=self.episode_id
            )
            
            reasoning = await self.world.execute_think(context)
            
            # Determine next action based on reasoning
            if "more information" in reasoning.lower() or "search" in reasoning.lower():
                result["next_agent"] = "searcher"
            elif "verify" in reasoning.lower():
                result["next_agent"] = "fact_checker"
            elif "sufficient" in reasoning.lower() or "synthesize" in reasoning.lower():
                result["next_agent"] = "answerer"
            else:
                result["next_agent"] = "searcher"
            
            result["reasoning"] = reasoning
        
        elif action_type == "verify":
            # Verify gathered information
            step = await self.react_loop.execute_step(
                self.current_agent,
                "Verify the gathered information",
                {"content": self.world.rag_context.get_content_summary() if self.world.rag_context else ""},
                episode_id=self.episode_id
            )
            
            result["verification"] = step.action
            result["next_agent"] = "answerer" if "verified" in step.action.lower() else "searcher"
        
        elif action_type == "synthesize":
            # This is handled in the main loop
            result["complete"] = True
        
        # Increment iteration
        if self.world.rag_context:
            self.world.rag_context.increment_iteration()
        
        return result
    
    async def _check_for_handoff(self, action_result: Dict[str, Any]) -> Optional[str]:
        """
        Check if action result indicates agent handoff.
        
        Args:
            action_result: Result from action execution
            
        Returns:
            Name of agent to handoff to, or None
        """
        return action_result.get("next_agent")
    
    async def _handoff_to_agent(self, agent_name: str) -> None:
        """
        Handoff control to another agent.
        
        Args:
            agent_name: Name of agent to handoff to
        """
        if agent_name in self.agents:
            # Transition world state
            await self.world.transition_to(RAGState.HANDING_OFF)
            
            # Switch agent
            self.current_agent = self.agents[agent_name]
            await self.world.assign_agent(agent_name)
            
            # Update handoff count
            self.handoff_count += 1
            
            # Transition to appropriate state for new agent
            if agent_name == "searcher":
                await self.world.transition_to(RAGState.SEARCHING)
            elif agent_name == "loader":
                await self.world.transition_to(RAGState.LOADING)
            elif agent_name == "thinker":
                await self.world.transition_to(RAGState.THINKING)
            elif agent_name == "fact_checker":
                await self.world.transition_to(RAGState.VERIFYING)
            elif agent_name == "answerer":
                await self.world.transition_to(RAGState.SYNTHESIZING)
            else:
                await self.world.transition_to(RAGState.THINKING)
    
    async def execute_simple_rag(self, query: str) -> str:
        """
        Execute a simplified RAG workflow for quick answers.
        
        Args:
            query: Question to answer
            
        Returns:
            Answer string
        """
        # Use simple team
        self.agents = RAGAgentFactory.create_simple_rag_team()
        
        # For simple RAG, start with searcher instead of router
        self.execution_id = f"simple_rag_{datetime.now().timestamp()}"
        self.start_time = datetime.now()
        
        # Generate episode ID for tracking (UUID v7 for TensorZero)
        import uuid_utils
        self.episode_id = str(uuid_utils.uuid7())
        
        # Initialize RAG context
        self.world.initialize_rag_context(query, max_iterations=5)
        
        # Start with searcher for simple queries
        self.current_agent = self.agents["searcher"]
        await self.world.assign_agent(self.current_agent.name)
        
        # Simple loop
        for iteration in range(5):
            # Search
            search_results = await self.world.execute_search(query)
            
            # Think
            self.current_agent = self.agents["thinker"]
            await self.world.assign_agent(self.current_agent.name)
            reasoning = await self.world.execute_think(str(search_results))
            
            # Check if ready to answer
            if "sufficient" in reasoning.lower() or iteration >= 3:
                break
        
        # Answer
        self.current_agent = self.agents["answerer"]
        await self.world.assign_agent(self.current_agent.name)
        answer = await self.world.execute_synthesize()
        
        return answer
    
    async def execute_research_rag(self, query: str) -> Dict[str, Any]:
        """
        Execute a research-focused RAG workflow.
        
        Args:
            query: Research question
            
        Returns:
            Detailed research results
        """
        # Use research team
        self.agents = RAGAgentFactory.create_research_team()
        
        # Thorough execution
        result = await self.answer_query(query, max_iterations=15, verbose=True)
        
        # Add research-specific metadata
        result["sources"] = []
        if self.world.rag_context:
            for content in self.world.rag_context.loaded_content:
                result["sources"].append({
                    "source": content["source"],
                    "relevance": content["relevance"],
                    "excerpt": content["content"][:200]
                })
        
        return result