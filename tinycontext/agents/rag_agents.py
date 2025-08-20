"""
RAG-specialized TinyPerson agents for information retrieval and synthesis.

These agents work together in a TinyWorld to perform multi-hop reasoning
and information gathering tasks.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from .loader import TinyPerson
import json


# RAG Agent Definitions
def create_searcher_agent() -> TinyPerson:
    """
    Creates a TinyPerson specialized in searching for information.
    """
    return TinyPerson(
        name="searcher",
        role="Information Searcher",
        prompts={
            "system": """You are a specialized search agent. Your role is to:
1. Analyze queries and identify key search terms
2. Determine the best search strategy (web, academic, code, etc.)
3. Formulate effective search queries
4. Evaluate if search results are sufficient

When you need to search, describe what you're looking for clearly.
If results are insufficient, suggest refined search terms.""",
            "user": "Search for information about: {query}"
        }
    )


def create_loader_agent() -> TinyPerson:
    """
    Creates a TinyPerson specialized in loading and extracting content.
    """
    return TinyPerson(
        name="loader",
        role="Content Loader",
        prompts={
            "system": """You are a content extraction specialist. Your role is to:
1. Load content from identified sources
2. Extract relevant sections
3. Clean and format the content
4. Identify key information and citations

When given a source, extract the most relevant information for the query at hand.
Preserve important details, dates, and citations.""",
            "user": "Load and extract content from: {source}"
        }
    )


def create_thinker_agent() -> TinyPerson:
    """
    Creates a TinyPerson specialized in reasoning about gathered information.
    """
    return TinyPerson(
        name="thinker",
        role="Strategic Thinker",
        prompts={
            "system": """You are a strategic reasoning agent. Your role is to:
1. Analyze gathered information holistically
2. Identify gaps in knowledge
3. Plan next steps for information gathering
4. Recognize when sufficient information is available
5. Connect disparate pieces of information

Think step-by-step about what you know and what you still need to find out.
Be explicit about your reasoning process.""",
            "user": "Analyze the current information and plan next steps: {context}"
        }
    )


def create_answerer_agent() -> TinyPerson:
    """
    Creates a TinyPerson specialized in synthesizing final answers.
    """
    return TinyPerson(
        name="answerer",
        role="Answer Synthesizer",
        prompts={
            "system": """You are an answer synthesis specialist. Your role is to:
1. Synthesize all gathered information into a comprehensive answer
2. Cite sources appropriately
3. Structure the answer clearly
4. Address all aspects of the original question
5. Indicate confidence level and any uncertainties

Provide clear, well-structured answers based on the accumulated evidence.""",
            "user": "Synthesize a final answer based on: {accumulated_context}"
        }
    )


def create_fact_checker_agent() -> TinyPerson:
    """
    Creates a TinyPerson specialized in verifying information.
    """
    return TinyPerson(
        name="fact_checker",
        role="Fact Verifier",
        prompts={
            "system": """You are a fact-checking specialist. Your role is to:
1. Verify claims against multiple sources
2. Identify contradictions or inconsistencies
3. Assess source reliability
4. Flag uncertain or disputed information
5. Suggest additional verification steps if needed

Be skeptical but fair. Focus on verifiable facts.""",
            "user": "Verify the following information: {claims}"
        }
    )


def create_router_agent() -> TinyPerson:
    """
    Creates a TinyPerson that routes queries to appropriate specialists.
    """
    return TinyPerson(
        name="router",
        role="Query Router",
        prompts={
            "system": """You are a query routing specialist. Your role is to:
1. Analyze incoming queries
2. Determine the type of information needed
3. Route to the appropriate specialist agent
4. Coordinate multi-agent workflows
5. Ensure efficient information flow

Route queries based on their complexity and information needs.
Simple lookups go to searcher, complex multi-hop queries need thinker first.""",
            "user": "Route this query to the appropriate agent: {query}"
        }
    )


@dataclass
class RAGContext:
    """
    Context maintained during RAG operations.
    """
    original_query: str
    search_history: List[Dict[str, Any]] = field(default_factory=list)
    loaded_content: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_steps: List[str] = field(default_factory=list)
    current_hypothesis: Optional[str] = None
    confidence_score: float = 0.0
    iteration_count: int = 0
    max_iterations: int = 10
    
    def add_search(self, query: str, results: List[str]) -> None:
        """Add a search operation to history."""
        self.search_history.append({
            "iteration": self.iteration_count,
            "query": query,
            "results": results,
            "timestamp": self._get_timestamp()
        })
    
    def add_content(self, source: str, content: str, relevance: float = 1.0) -> None:
        """Add loaded content to the context."""
        self.loaded_content.append({
            "source": source,
            "content": content[:5000],  # Limit content size
            "relevance": relevance,
            "iteration": self.iteration_count,
            "timestamp": self._get_timestamp()
        })
    
    def add_reasoning(self, step: str) -> None:
        """Add a reasoning step."""
        self.reasoning_steps.append(f"[Iteration {self.iteration_count}] {step}")
    
    def increment_iteration(self) -> bool:
        """Increment iteration counter and check if we should continue."""
        self.iteration_count += 1
        return self.iteration_count < self.max_iterations
    
    def get_accumulated_knowledge(self) -> str:
        """Get a summary of all accumulated knowledge."""
        knowledge = {
            "query": self.original_query,
            "searches_performed": len(self.search_history),
            "sources_loaded": len(self.loaded_content),
            "reasoning_steps": self.reasoning_steps,
            "current_hypothesis": self.current_hypothesis,
            "confidence": self.confidence_score
        }
        return json.dumps(knowledge, indent=2)
    
    def get_search_queries(self) -> List[str]:
        """Get all search queries performed."""
        return [s["query"] for s in self.search_history]
    
    def get_content_summary(self) -> str:
        """Get a summary of loaded content."""
        if not self.loaded_content:
            return "No content loaded yet."
        
        summary = []
        for content in self.loaded_content[-3:]:  # Last 3 sources
            summary.append(f"Source: {content['source']}\nContent: {content['content'][:500]}...")
        
        return "\n\n".join(summary)
    
    def should_continue(self) -> bool:
        """Determine if we should continue gathering information."""
        # Stop if we have high confidence
        if self.confidence_score > 0.85:
            return False
        
        # Stop if we've hit iteration limit
        if self.iteration_count >= self.max_iterations:
            return False
        
        # Continue if we have few sources
        if len(self.loaded_content) < 2:
            return True
        
        # Continue if recent searches are finding new info
        if len(self.search_history) > 0:
            recent_results = self.search_history[-1].get("results", [])
            if len(recent_results) > 0:
                return True
        
        return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


class RAGAgentFactory:
    """
    Factory for creating and managing RAG agents.
    """
    
    @staticmethod
    def create_rag_team() -> Dict[str, TinyPerson]:
        """
        Create a complete team of RAG agents.
        
        Returns:
            Dictionary mapping role names to TinyPerson agents
        """
        return {
            "router": create_router_agent(),
            "searcher": create_searcher_agent(),
            "loader": create_loader_agent(),
            "thinker": create_thinker_agent(),
            "answerer": create_answerer_agent(),
            "fact_checker": create_fact_checker_agent()
        }
    
    @staticmethod
    def create_simple_rag_team() -> Dict[str, TinyPerson]:
        """
        Create a minimal RAG team for simple queries.
        
        Returns:
            Dictionary with essential RAG agents
        """
        return {
            "searcher": create_searcher_agent(),
            "thinker": create_thinker_agent(),
            "answerer": create_answerer_agent()
        }
    
    @staticmethod
    def create_research_team() -> Dict[str, TinyPerson]:
        """
        Create a research-focused RAG team.
        
        Returns:
            Dictionary with research-oriented agents
        """
        # Create base agents
        team = {
            "router": create_router_agent(),
            "searcher": create_searcher_agent(),
            "loader": create_loader_agent(),
            "thinker": create_thinker_agent(),
            "fact_checker": create_fact_checker_agent(),
            "answerer": create_answerer_agent()
        }
        
        # Customize for research by modifying system prompts
        team["searcher"].prompts.system += """
Focus on academic sources, research papers, and authoritative references.
Prioritize peer-reviewed content and primary sources."""
        
        team["fact_checker"].prompts.system += """
Pay special attention to citations, methodology, and statistical claims.
Verify against multiple academic sources when possible."""
        
        return team