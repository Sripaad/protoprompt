"""
RAG-extended TinyWorld with information retrieval states and transitions.

Extends AsyncTinyWorld to support RAG operations through FSM states.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field

from .async_tiny_world import AsyncTinyWorld, AgentState
from ..agents.rag_agents import RAGContext


class RAGState(Enum):
    """Extended states for RAG operations."""
    IDLE = "idle"
    ROUTING = "routing"           # Determining query type and approach
    SEARCHING = "searching"        # Searching for information
    LOADING = "loading"           # Loading content from sources
    THINKING = "thinking"         # Reasoning about information
    VERIFYING = "verifying"       # Fact-checking information
    SYNTHESIZING = "synthesizing" # Creating final answer
    HANDING_OFF = "handing_off"   # Transferring to another agent
    COMPLETE = "complete"         # Task completed
    ERROR = "error"              # Error state


@dataclass
class RAGAction:
    """Represents a RAG-specific action."""
    action_type: str  # search, load, think, verify, synthesize
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)
    agent: Optional[str] = None
    confidence: float = 0.0


class AsyncRAGWorld(AsyncTinyWorld):
    """
    Extended TinyWorld for RAG operations with information retrieval capabilities.
    """
    
    def __init__(self, world_id: str = None):
        """
        Initialize RAG world with extended capabilities.
        
        Args:
            world_id: Unique identifier for this world
        """
        super().__init__(world_id)
        
        # RAG-specific context
        self.rag_context: Optional[RAGContext] = None
        self.message_history: List[Dict[str, Any]] = []
        self.action_history: List[RAGAction] = []
        self.current_agent: Optional[str] = None
        
        # RAG state mappings (extend base FSM)
        self.rag_transitions = {
            RAGState.IDLE: [RAGState.ROUTING, RAGState.SEARCHING],
            RAGState.ROUTING: [RAGState.SEARCHING, RAGState.THINKING, RAGState.LOADING],
            RAGState.SEARCHING: [RAGState.LOADING, RAGState.THINKING, RAGState.HANDING_OFF],
            RAGState.LOADING: [RAGState.THINKING, RAGState.VERIFYING, RAGState.SEARCHING],
            RAGState.THINKING: [RAGState.SEARCHING, RAGState.LOADING, RAGState.SYNTHESIZING, RAGState.HANDING_OFF],
            RAGState.VERIFYING: [RAGState.THINKING, RAGState.SEARCHING, RAGState.SYNTHESIZING],
            RAGState.SYNTHESIZING: [RAGState.COMPLETE, RAGState.VERIFYING, RAGState.THINKING],
            RAGState.HANDING_OFF: [RAGState.ROUTING, RAGState.SEARCHING, RAGState.THINKING],
            RAGState.COMPLETE: [RAGState.IDLE],
            RAGState.ERROR: [RAGState.IDLE, RAGState.THINKING]
        }
        
        # Action handlers
        self.action_handlers: Dict[str, Callable] = {}
        
        # Performance metrics
        self.search_count = 0
        self.load_count = 0
        self.think_count = 0
        self.total_tokens = 0
    
    def initialize_rag_context(self, query: str, max_iterations: int = 10) -> None:
        """
        Initialize RAG context for a new query.
        
        Args:
            query: The original query to answer
            max_iterations: Maximum number of reasoning iterations
        """
        self.rag_context = RAGContext(
            original_query=query,
            max_iterations=max_iterations
        )
        self.message_history = [{
            "role": "user",
            "content": query,
            "timestamp": datetime.now().isoformat()
        }]
    
    async def execute_search(self, query: str, search_type: str = "general") -> List[str]:
        """
        Execute a search action in the SEARCHING state.
        
        Args:
            query: Search query
            search_type: Type of search (web, academic, code, etc.)
            
        Returns:
            List of search results
        """
        if self.current_state not in [AgentState.ACTING, RAGState.SEARCHING]:
            await self.transition_to(RAGState.SEARCHING)
        
        # Record action
        action = RAGAction(
            action_type="search",
            parameters={"query": query, "type": search_type},
            agent=self.current_agent
        )
        
        # In a real implementation, this would call actual search APIs
        # For now, return simulated results
        results = [
            f"Result 1 for '{query}': Relevant information about the topic",
            f"Result 2 for '{query}': Additional context and details",
            f"Result 3 for '{query}': Supporting evidence and examples"
        ]
        
        action.result = results
        action.confidence = 0.7
        self.action_history.append(action)
        
        # Update RAG context
        if self.rag_context:
            self.rag_context.add_search(query, results)
        
        # Update metrics
        self.search_count += 1
        
        # Add to message history
        self.message_history.append({
            "role": "assistant",
            "content": f"Searched for: {query}\nFound {len(results)} results",
            "action": "search",
            "timestamp": datetime.now().isoformat()
        })
        
        return results
    
    async def execute_load(self, source: str) -> str:
        """
        Execute a content loading action in the LOADING state.
        
        Args:
            source: Source to load content from
            
        Returns:
            Loaded content
        """
        if self.current_state != RAGState.LOADING:
            await self.transition_to(RAGState.LOADING)
        
        # Record action
        action = RAGAction(
            action_type="load",
            parameters={"source": source},
            agent=self.current_agent
        )
        
        # Simulate content loading
        content = f"""Content from {source}:
        This is detailed information extracted from the source.
        It contains relevant facts, data, and explanations.
        The content helps answer the user's query comprehensively."""
        
        action.result = content
        action.confidence = 0.8
        self.action_history.append(action)
        
        # Update RAG context
        if self.rag_context:
            self.rag_context.add_content(source, content)
        
        # Update metrics
        self.load_count += 1
        
        # Add to message history
        self.message_history.append({
            "role": "assistant",
            "content": f"Loaded content from: {source}",
            "action": "load",
            "timestamp": datetime.now().isoformat()
        })
        
        return content
    
    async def execute_think(self, context: str) -> str:
        """
        Execute a thinking/reasoning action in the THINKING state.
        
        Args:
            context: Current context to reason about
            
        Returns:
            Reasoning output
        """
        if self.current_state != RAGState.THINKING:
            await self.transition_to(RAGState.THINKING)
        
        # Record action
        action = RAGAction(
            action_type="think",
            parameters={"context": context[:500]},  # Limit context size
            agent=self.current_agent
        )
        
        # Generate reasoning
        reasoning = f"""Based on the current information:
        1. We have gathered {len(self.action_history)} pieces of information
        2. The query requires {'simple' if self.search_count < 2 else 'complex'} analysis
        3. {'More information needed' if self.rag_context and self.rag_context.confidence_score < 0.7 else 'Sufficient information gathered'}
        4. Next step: {'search for more' if self.search_count < 3 else 'synthesize answer'}"""
        
        action.result = reasoning
        action.confidence = 0.75
        self.action_history.append(action)
        
        # Update RAG context
        if self.rag_context:
            self.rag_context.add_reasoning(reasoning)
            self.rag_context.confidence_score = min(0.9, self.rag_context.confidence_score + 0.1)
        
        # Update metrics
        self.think_count += 1
        
        # Add to message history
        self.message_history.append({
            "role": "assistant",
            "content": f"Thinking: {reasoning[:200]}...",
            "action": "think",
            "timestamp": datetime.now().isoformat()
        })
        
        return reasoning
    
    async def execute_synthesize(self) -> str:
        """
        Synthesize final answer from accumulated information.
        
        Returns:
            Final synthesized answer
        """
        if self.current_state != RAGState.SYNTHESIZING:
            await self.transition_to(RAGState.SYNTHESIZING)
        
        # Gather all information
        if not self.rag_context:
            return "No context available for synthesis"
        
        # Create synthesis action
        action = RAGAction(
            action_type="synthesize",
            parameters={"context": self.rag_context.get_accumulated_knowledge()},
            agent=self.current_agent
        )
        
        # Generate answer based on accumulated context
        answer = f"""Based on my research regarding '{self.rag_context.original_query}':

**Summary:**
After conducting {self.search_count} searches and analyzing {self.load_count} sources, here's what I found:

**Key Findings:**
{self.rag_context.get_content_summary()}

**Reasoning Process:**
{' → '.join(self.rag_context.reasoning_steps[-3:]) if self.rag_context.reasoning_steps else 'Direct analysis'}

**Conclusion:**
The answer addresses the query with {self.rag_context.confidence_score:.0%} confidence based on the gathered information.

**Sources Consulted:** {len(self.rag_context.loaded_content)} documents
**Iterations Required:** {self.rag_context.iteration_count}
"""
        
        action.result = answer
        action.confidence = self.rag_context.confidence_score
        self.action_history.append(action)
        
        # Add to message history
        self.message_history.append({
            "role": "assistant",
            "content": answer,
            "action": "answer",
            "timestamp": datetime.now().isoformat()
        })
        
        # Transition to complete
        await self.transition_to(RAGState.COMPLETE)
        
        return answer
    
    async def should_continue_gathering(self) -> bool:
        """
        Determine if more information gathering is needed.
        
        Returns:
            True if should continue, False otherwise
        """
        if not self.rag_context:
            return False
        
        return self.rag_context.should_continue()
    
    def get_message_history(self) -> List[Dict[str, Any]]:
        """
        Get the complete message history.
        
        Returns:
            List of messages in the conversation
        """
        return self.message_history.copy()
    
    def get_action_summary(self) -> Dict[str, Any]:
        """
        Get summary of all RAG actions taken.
        
        Returns:
            Summary dictionary
        """
        return {
            "total_actions": len(self.action_history),
            "searches": self.search_count,
            "loads": self.load_count,
            "thinks": self.think_count,
            "confidence": self.rag_context.confidence_score if self.rag_context else 0,
            "iterations": self.rag_context.iteration_count if self.rag_context else 0,
            "action_types": {
                "search": sum(1 for a in self.action_history if a.action_type == "search"),
                "load": sum(1 for a in self.action_history if a.action_type == "load"),
                "think": sum(1 for a in self.action_history if a.action_type == "think"),
                "synthesize": sum(1 for a in self.action_history if a.action_type == "synthesize")
            }
        }
    
    async def transition_to_rag_state(self, state: RAGState, metadata: Dict[str, Any] = None) -> bool:
        """
        Transition to a RAG-specific state.
        
        Args:
            state: Target RAG state
            metadata: Additional transition metadata
            
        Returns:
            True if transition successful
        """
        # Map RAG states to base FSM states where applicable
        state_mapping = {
            RAGState.IDLE: AgentState.IDLE,
            RAGState.THINKING: AgentState.THINKING,
            RAGState.SEARCHING: AgentState.ACTING,
            RAGState.LOADING: AgentState.ACTING,
            RAGState.VERIFYING: AgentState.THINKING,
            RAGState.SYNTHESIZING: AgentState.ACTING,
            RAGState.HANDING_OFF: AgentState.HANDING_OFF,
            RAGState.ERROR: AgentState.ERROR
        }
        
        # Use base transition for mapped states
        if state in state_mapping:
            base_state = state_mapping[state]
            success = await self.transition_to(base_state, metadata=metadata)
            
            # Store RAG-specific state info
            if success and metadata:
                metadata["rag_state"] = state.value
            
            return success
        
        return False
    
    def register_action_handler(self, action_type: str, handler: Callable) -> None:
        """
        Register a custom action handler.
        
        Args:
            action_type: Type of action to handle
            handler: Async callable to handle the action
        """
        self.action_handlers[action_type] = handler
    
    async def execute_custom_action(self, action_type: str, **kwargs) -> Any:
        """
        Execute a custom registered action.
        
        Args:
            action_type: Type of action to execute
            **kwargs: Action parameters
            
        Returns:
            Action result
        """
        if action_type in self.action_handlers:
            handler = self.action_handlers[action_type]
            return await handler(**kwargs)
        
        raise ValueError(f"No handler registered for action type: {action_type}")
    
    async def assign_agent(self, agent_name: str) -> None:
        """
        Assign an agent to this world.
        
        Args:
            agent_name: Name of the agent to assign
        """
        self.current_agent = agent_name
        # Could also update state metadata
        if hasattr(self, 'state_metadata'):
            self.state_metadata['current_agent'] = agent_name