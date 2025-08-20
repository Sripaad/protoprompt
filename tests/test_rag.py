#!/usr/bin/env python3
"""
Simple test script for RAG functionality.
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from tinycontext.orchestration.rag_orchestrator import RAGOrchestrator
from tinycontext.inference.tensorzero_client import AsyncTensorZeroClient


async def test_simple_query():
    """Test a simple RAG query."""
    print("\n" + "="*60)
    print("Testing Simple RAG Query")
    print("="*60)
    
    # Initialize
    llm_client = AsyncTensorZeroClient(use_embedded=False)
    await llm_client.initialize()
    
    orchestrator = RAGOrchestrator(llm_client=llm_client)
    await orchestrator.initialize()
    
    # Simple query
    query = "What is async programming?"
    print(f"\nQuery: {query}")
    
    # Execute
    answer = await orchestrator.execute_simple_rag(query)
    
    print(f"\nAnswer Preview:")
    print(answer[:500] + "..." if len(answer) > 500 else answer)
    
    await llm_client.close()


async def test_multi_hop_query():
    """Test a multi-hop RAG query."""
    print("\n" + "="*60)
    print("Testing Multi-Hop RAG Query")
    print("="*60)
    
    # Initialize
    llm_client = AsyncTensorZeroClient(use_embedded=False)
    await llm_client.initialize()
    
    orchestrator = RAGOrchestrator(llm_client=llm_client)
    await orchestrator.initialize()
    
    # Complex query
    query = "Who invented Python and what other projects are they known for?"
    print(f"\nQuery: {query}")
    print("This requires:")
    print("1. Identify Python's inventor")
    print("2. Research their other projects")
    
    # Execute with limited iterations for testing
    result = await orchestrator.answer_query(query, max_iterations=5, verbose=True)
    
    print(f"\nExecution Stats:")
    print(f"  Iterations: {result['iterations']}")
    print(f"  Handoffs: {result['handoffs']}")
    print(f"  Confidence: {result['confidence']:.0%}")
    print(f"  Time: {result['execution_time']:.2f}s")
    
    await llm_client.close()


async def test_agent_states():
    """Test RAG world state transitions."""
    print("\n" + "="*60)
    print("Testing RAG World States")
    print("="*60)
    
    from tinycontext.core.rag_world import AsyncRAGWorld, RAGState
    from tinycontext.agents.rag_agents import RAGAgentFactory
    
    # Create world and agents
    world = AsyncRAGWorld("test_world")
    agents = RAGAgentFactory.create_simple_rag_team()
    
    # Initialize with query
    world.initialize_rag_context("Test query")
    
    print("\nState Transitions:")
    
    # Test transitions
    states = [
        (RAGState.IDLE, "Starting"),
        (RAGState.SEARCHING, "Searching"),
        (RAGState.THINKING, "Thinking"),
        (RAGState.SYNTHESIZING, "Synthesizing"),
        (RAGState.COMPLETE, "Complete")
    ]
    
    for state, action in states:
        success = await world.transition_to_rag_state(state)
        print(f"  {state.value}: {'✓' if success else '✗'} - {action}")
    
    # Test actions
    print("\nRAG Actions:")
    
    # Search
    results = await world.execute_search("test query")
    print(f"  Search: Found {len(results)} results")
    
    # Load
    content = await world.execute_load("test_source")
    print(f"  Load: Loaded {len(content)} chars")
    
    # Think
    reasoning = await world.execute_think("test context")
    print(f"  Think: Generated reasoning")
    
    # Get summary
    summary = world.get_action_summary()
    print(f"\nAction Summary:")
    print(f"  Total: {summary['total_actions']}")
    print(f"  Searches: {summary['searches']}")
    print(f"  Loads: {summary['loads']}")
    print(f"  Thinks: {summary['thinks']}")


async def main():
    """Run all tests."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                    TinyContext RAG Test Suite                  ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Test individual components
    await test_agent_states()
    
    # Test simple query
    await test_simple_query()
    
    # Test multi-hop query
    await test_multi_hop_query()
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║                      All Tests Complete! ✓                     ║
╚════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    asyncio.run(main())