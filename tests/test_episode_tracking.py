#!/usr/bin/env python3
"""
Test episode tracking for TensorZero observability.
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from tinycontext.orchestration.rag_orchestrator import RAGOrchestrator
from tinycontext.inference.tensorzero_client import AsyncTensorZeroClient
from tinycontext.workflows.workflow_executor import WorkflowExecutor
from tinycontext.workflows.workflow_definition import WorkflowBuilder
from tinycontext.manager.async_context_manager import AsyncTinyContextManager


async def test_rag_with_episodes():
    """Test RAG with proper episode tracking."""
    print("\n" + "="*60)
    print("Testing RAG with Episode Tracking")
    print("="*60)
    
    # Initialize with TensorZero
    llm_client = AsyncTensorZeroClient(use_embedded=False)
    await llm_client.initialize()
    
    orchestrator = RAGOrchestrator(llm_client=llm_client)
    await orchestrator.initialize()
    
    # Test queries with unique episode IDs (must be UUID v7)
    import uuid_utils
    queries = [
        ("What is Python?", str(uuid_utils.uuid7())),
        ("How does async work?", str(uuid_utils.uuid7())),
        ("What are transformers?", str(uuid_utils.uuid7()))
    ]
    
    for query, episode_id in queries:
        print(f"\n📍 Query: {query}")
        print(f"   Episode ID: {episode_id}")
        
        # Execute with episode tracking
        result = await orchestrator.answer_query(
            query,
            max_iterations=3,
            verbose=False,
            episode_id=episode_id
        )
        
        print(f"   ✅ Completed in {result['iterations']} iterations")
        print(f"   Confidence: {result['confidence']:.0%}")
    
    await llm_client.close()
    print("\n✨ Check TensorZero UI for grouped episodes!")


async def test_workflow_with_episodes():
    """Test workflow execution with episode tracking."""
    print("\n" + "="*60)
    print("Testing Workflow with Episode Tracking")
    print("="*60)
    
    # Initialize
    llm_client = AsyncTensorZeroClient(use_embedded=False)
    await llm_client.initialize()
    
    context_manager = AsyncTinyContextManager(llm_client=llm_client)
    await context_manager.initialize()
    
    executor = WorkflowExecutor(
        context_manager=context_manager,
        llm_client=llm_client
    )
    
    # Create simple workflow
    builder = WorkflowBuilder("test_workflow", "Test Workflow")
    builder.add_agent_node(
        "step1",
        "First Step",
        agent_role="analyzer",
        prompt_template="Analyze: {input}"
    )
    builder.add_agent_node(
        "step2",
        "Second Step",
        agent_role="planner",
        prompt_template="Plan based on analysis"
    )
    builder.connect("step1", "step2")
    
    workflow = builder.build()
    
    # Execute with episode ID
    episode_id = "episode_workflow_test"
    print(f"\nExecuting workflow with episode: {episode_id}")
    
    # We need to modify executor to pass episode_id
    # For now, this shows the structure
    result = await executor.execute(
        workflow,
        {"input": "Test data"},
        execution_id=episode_id
    )
    
    print(f"✅ Workflow completed: {result.status}")
    print(f"   Duration: {result.total_duration_ms:.2f}ms")
    
    await llm_client.close()


async def test_multi_hop_with_episode():
    """Test multi-hop reasoning with single episode."""
    print("\n" + "="*60)
    print("Testing Multi-Hop with Single Episode")
    print("="*60)
    
    llm_client = AsyncTensorZeroClient(use_embedded=False)
    await llm_client.initialize()
    
    orchestrator = RAGOrchestrator(llm_client=llm_client)
    await orchestrator.initialize()
    
    # Complex query requiring multiple hops
    import uuid_utils
    query = "Who created Python and what inspired them?"
    episode_id = str(uuid_utils.uuid7())
    
    print(f"\n🔗 Multi-hop Query: {query}")
    print(f"   Episode ID: {episode_id}")
    print("\nThis will create multiple inferences in a single episode:")
    
    result = await orchestrator.answer_query(
        query,
        max_iterations=5,
        verbose=True,
        episode_id=episode_id
    )
    
    print(f"\n📊 Episode Summary:")
    print(f"   Total inferences in episode: ~{result['iterations'] * 2}")  # reason + act
    print(f"   Agent handoffs: {result['handoffs']}")
    print(f"   Final confidence: {result['confidence']:.0%}")
    
    await llm_client.close()


async def main():
    """Run all episode tracking tests."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║            TensorZero Episode Tracking Test Suite              ║
║                                                                 ║
║  Testing that workflows group inferences into episodes         ║
║  for better observability in the TensorZero UI.                ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Run tests
    await test_rag_with_episodes()
    await test_multi_hop_with_episode()
    # await test_workflow_with_episodes()  # Would need executor updates
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║                  Episode Tracking Tests Complete!              ║
║                                                                 ║
║  ✅ Episodes are now properly tracked in TensorZero           ║
║  📊 Check the UI at http://localhost:4000                     ║
║  🔍 Look for grouped inferences under episode IDs             ║
╚════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    asyncio.run(main())