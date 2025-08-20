#!/usr/bin/env python3
"""
Demonstration of RAG (Retrieval-Augmented Generation) using TinyPerson agents.

Shows how multiple specialized agents work together in a TinyWorld to:
1. Search for information
2. Load and extract content
3. Think and reason about findings
4. Synthesize comprehensive answers

This mirrors the TensorZero RAG example but uses TinyContext's multi-agent approach.
"""

import asyncio
import json
from pathlib import Path
import sys
from datetime import datetime
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tinycontext.orchestration.rag_orchestrator import RAGOrchestrator
from tinycontext.agents.rag_agents import RAGAgentFactory
from tinycontext.inference.tensorzero_client import AsyncTensorZeroClient
from tinycontext.core.rag_world import AsyncRAGWorld, RAGState


async def demonstrate_simple_rag():
    """
    Demonstrate a simple RAG query answering.
    """
    print("\n" + "="*70)
    print("📚 Simple RAG Demo: Quick Information Retrieval")
    print("="*70)
    
    # Initialize components
    llm_client = AsyncTensorZeroClient(use_embedded=False)
    await llm_client.initialize()
    
    orchestrator = RAGOrchestrator(llm_client=llm_client)
    await orchestrator.initialize()
    
    # Simple query
    query = "What are the key principles of async programming in Python?"
    
    print(f"\n❓ Query: {query}")
    print("\n🔄 Processing with TinyPerson agents...\n")
    
    # Execute simple RAG
    answer = await orchestrator.execute_simple_rag(query)
    
    print("\n💡 Answer:")
    print(answer)
    
    await llm_client.close()


async def demonstrate_multi_hop_rag():
    """
    Demonstrate multi-hop reasoning similar to TensorZero's example.
    
    This shows how agents collaborate to answer complex queries that require
    multiple steps of information gathering.
    """
    print("\n" + "="*70)
    print("🔗 Multi-Hop RAG Demo: Complex Query Resolution")
    print("="*70)
    
    # Initialize components
    llm_client = AsyncTensorZeroClient(use_embedded=False)
    await llm_client.initialize()
    
    orchestrator = RAGOrchestrator(llm_client=llm_client)
    await orchestrator.initialize()
    
    # Complex multi-hop query (similar to TensorZero example)
    query = "What is a common dish in the hometown of the scientist who discovered the electron?"
    
    print(f"\n❓ Complex Query: {query}")
    print("\nThis requires multiple steps:")
    print("1. Identify the scientist who discovered the electron")
    print("2. Find their hometown")
    print("3. Research common dishes from that location")
    print("\n🔄 Processing with TinyPerson agents...\n")
    
    # Execute with verbose output to show the process
    result = await orchestrator.answer_query(query, max_iterations=10, verbose=True)
    
    print("\n📊 Execution Summary:")
    print(f"   Total iterations: {result['iterations']}")
    print(f"   Agent handoffs: {result['handoffs']}")
    print(f"   Execution time: {result['execution_time']:.2f}s")
    print(f"   Final confidence: {result['confidence']:.0%}")
    
    print("\n📈 Action Breakdown:")
    for action_type, count in result['actions']['action_types'].items():
        print(f"   {action_type}: {count}")
    
    await llm_client.close()


async def demonstrate_research_rag():
    """
    Demonstrate research-focused RAG with fact-checking.
    """
    print("\n" + "="*70)
    print("🔬 Research RAG Demo: Academic Information Gathering")
    print("="*70)
    
    # Initialize components
    llm_client = AsyncTensorZeroClient(use_embedded=False)
    await llm_client.initialize()
    
    orchestrator = RAGOrchestrator(llm_client=llm_client)
    await orchestrator.initialize()
    
    # Research query
    query = "What are the latest advances in transformer architectures for LLMs in 2024?"
    
    print(f"\n❓ Research Query: {query}")
    print("\n🔄 Executing research workflow with fact-checking...\n")
    
    # Execute research RAG
    result = await orchestrator.execute_research_rag(query)
    
    print("\n📚 Research Results:")
    print(f"\n{result['answer']}")
    
    if result.get('sources'):
        print("\n📖 Sources Consulted:")
        for i, source in enumerate(result['sources'][:5], 1):
            print(f"\n{i}. {source['source']}")
            print(f"   Relevance: {source['relevance']:.0%}")
            print(f"   Excerpt: {source['excerpt']}...")
    
    await llm_client.close()


async def demonstrate_agent_collaboration():
    """
    Demonstrate how TinyPerson agents collaborate in a RAG world.
    """
    print("\n" + "="*70)
    print("🤝 Agent Collaboration Demo: TinyPerson Team in Action")
    print("="*70)
    
    # Create RAG world
    world = AsyncRAGWorld(world_id="demo_world")
    
    # Create RAG agents
    agents = RAGAgentFactory.create_rag_team()
    
    print("\n👥 RAG Team Members:")
    for name, agent in agents.items():
        print(f"   • {name}: {agent.role}")
    
    # Initialize world with a query
    query = "How do async workflows improve system performance?"
    world.initialize_rag_context(query)
    
    print(f"\n❓ Query: {query}")
    print("\n🌍 TinyWorld FSM States:")
    
    # Demonstrate state transitions
    states_demo = [
        (RAGState.IDLE, "router", "Starting RAG workflow"),
        (RAGState.ROUTING, "router", "Analyzing query complexity"),
        (RAGState.SEARCHING, "searcher", "Searching for relevant information"),
        (RAGState.LOADING, "loader", "Loading content from sources"),
        (RAGState.THINKING, "thinker", "Reasoning about gathered information"),
        (RAGState.VERIFYING, "fact_checker", "Verifying key facts"),
        (RAGState.SYNTHESIZING, "answerer", "Creating final answer"),
        (RAGState.COMPLETE, None, "Task completed")
    ]
    
    for state, agent_name, description in states_demo:
        if agent_name:
            await world.assign_agent(agent_name)
        
        # Transition to state
        if state == RAGState.IDLE:
            await world.transition_to_rag_state(state)
        else:
            await world.transition_to_rag_state(state, {"reason": description})
        
        print(f"\n   📍 State: {state.value}")
        print(f"      Agent: {agent_name or 'None'}")
        print(f"      Action: {description}")
        
        # Simulate some work in each state
        await asyncio.sleep(0.1)
    
    print("\n✅ Workflow demonstration complete!")
    
    # Show world summary
    action_summary = world.get_action_summary()
    print("\n📊 World Statistics:")
    print(f"   Total actions: {action_summary['total_actions']}")
    print(f"   Searches: {action_summary['searches']}")
    print(f"   Content loads: {action_summary['loads']}")
    print(f"   Think operations: {action_summary['thinks']}")


async def demonstrate_custom_rag_workflow():
    """
    Demonstrate building a custom RAG workflow.
    """
    print("\n" + "="*70)
    print("🛠️ Custom RAG Workflow Demo: Wikipedia-style Information Gathering")
    print("="*70)
    
    # This mimics the TensorZero Wikipedia RAG example
    
    # Initialize components
    llm_client = AsyncTensorZeroClient(use_embedded=False)
    await llm_client.initialize()
    
    orchestrator = RAGOrchestrator(llm_client=llm_client)
    await orchestrator.initialize()
    
    # Register custom action handlers (like Wikipedia search/load)
    async def wikipedia_search(query: str) -> List[str]:
        """Simulate Wikipedia search."""
        return [
            f"Wikipedia: {query} (Main article)",
            f"Wikipedia: History of {query}",
            f"Wikipedia: {query} in modern context"
        ]
    
    async def wikipedia_load(page: str) -> str:
        """Simulate loading Wikipedia page."""
        return f"""Content from {page}:
        This is detailed information about the topic.
        It includes historical context, current applications, and future directions.
        The article provides comprehensive coverage with citations and references."""
    
    # Register handlers
    orchestrator.world.register_action_handler("wikipedia_search", wikipedia_search)
    orchestrator.world.register_action_handler("wikipedia_load", wikipedia_load)
    
    # Query similar to TensorZero example
    queries = [
        "What is the capital of the country that hosted the 2024 Olympics?",
        "Who wrote the book that inspired the movie 'Blade Runner'?",
        "What programming language was created by Guido van Rossum?"
    ]
    
    for query in queries:
        print(f"\n❓ Query: {query}")
        
        # Custom execution using registered handlers
        result = await orchestrator.answer_query(query, max_iterations=5, verbose=False)
        
        print(f"✅ Answer: {result['answer'][:300]}...")
        print(f"   Confidence: {result['confidence']:.0%}")
        print(f"   Iterations: {result['iterations']}")
    
    await llm_client.close()


async def main():
    """
    Main demonstration function.
    """
    print("""
╔════════════════════════════════════════════════════════════════════╗
║     TinyContext RAG Demo: Multi-Agent Information Retrieval       ║
║                                                                    ║
║  Demonstrating how TinyPerson agents collaborate in a TinyWorld   ║
║  to perform Retrieval-Augmented Generation (RAG) workflows.       ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run demonstrations
    await demonstrate_agent_collaboration()
    await demonstrate_simple_rag()
    await demonstrate_multi_hop_rag()
    await demonstrate_research_rag()
    await demonstrate_custom_rag_workflow()
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                     RAG Demo Complete! 🎉                         ║
║                                                                    ║
║  Key Concepts Demonstrated:                                       ║
║  • TinyPerson agents with specialized RAG roles                   ║
║  • AsyncRAGWorld managing information retrieval states            ║
║  • Multi-hop reasoning through agent handoffs                     ║
║  • Message history and context accumulation                       ║
║  • Custom action handlers for different data sources              ║
║                                                                    ║
║  The entire RAG workflow emerges from TinyPerson collaboration!   ║
╚════════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    asyncio.run(main())