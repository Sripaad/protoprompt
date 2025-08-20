#!/usr/bin/env python3
"""
Async TensorZero Integration Example.

Demonstrates direct usage of AsyncTensorZeroClient for concurrent LLM calls.
"""

import asyncio
import time
from typing import List, Dict, Any
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tinycontext.inference.tensorzero_client import AsyncTensorZeroClient


async def basic_concurrent_calls():
    """Demonstrate basic concurrent LLM calls."""
    print("🚀 Basic Concurrent Calls Demo")
    print("=" * 50)
    
    # Initialize client
    client = AsyncTensorZeroClient()
    await client.initialize()
    
    # Define multiple reasoning tasks
    reasoning_tasks = [
        {
            "function": "tiny_reasoning",
            "kwargs": {
                "input_text": "How can we improve customer retention?",
                "agent_role": "business strategist",
                "system_prompt": "You are a business strategy expert."
            }
        },
        {
            "function": "tiny_reasoning",
            "kwargs": {
                "input_text": "What metrics should we track for success?",
                "agent_role": "data analyst",
                "system_prompt": "You are a data-driven analyst."
            }
        },
        {
            "function": "tiny_reasoning",
            "kwargs": {
                "input_text": "How do we implement the technical solution?",
                "agent_role": "software architect",
                "system_prompt": "You are a technical architect."
            }
        }
    ]
    
    print("\n📋 Concurrent Reasoning Tasks:")
    for i, task in enumerate(reasoning_tasks, 1):
        print(f"   {i}. [{task['kwargs']['agent_role']}] {task['kwargs']['input_text']}")
    
    print("\n⚡ Executing concurrently...")
    start_time = time.time()
    
    # Execute all tasks concurrently
    responses = await client.call_concurrent(reasoning_tasks)
    
    elapsed = time.time() - start_time
    
    print(f"\n✅ Completed in {elapsed:.2f} seconds")
    print("\n📊 Results:")
    print("-" * 50)
    
    for i, (task, response) in enumerate(zip(reasoning_tasks, responses), 1):
        role = task['kwargs']['agent_role']
        print(f"\n{i}. {role}:")
        print(f"   {response[:200]}...")
    
    # Cleanup
    await client.close()


async def reasoning_to_action_pipeline():
    """Demonstrate a reasoning-to-action pipeline."""
    print("\n" + "=" * 50)
    print("🔄 Reasoning-to-Action Pipeline Demo")
    print("=" * 50)
    
    # Initialize client
    client = AsyncTensorZeroClient()
    await client.initialize()
    
    # Step 1: Concurrent reasoning for different aspects
    print("\n📍 Step 1: Parallel Reasoning")
    
    reasoning_calls = [
        {
            "function": "tiny_reasoning",
            "kwargs": {
                "input_text": "Design a scalable microservices architecture",
                "agent_role": "system architect"
            }
        },
        {
            "function": "tiny_reasoning",
            "kwargs": {
                "input_text": "Plan the deployment strategy",
                "agent_role": "devops engineer"
            }
        },
        {
            "function": "tiny_reasoning",
            "kwargs": {
                "input_text": "Identify potential security concerns",
                "agent_role": "security analyst"
            }
        }
    ]
    
    # Execute reasoning concurrently
    reasoning_results = await client.call_concurrent(reasoning_calls)
    
    print("   ✓ Reasoning complete for all aspects")
    
    # Step 2: Generate actions based on reasoning
    print("\n📍 Step 2: Parallel Action Generation")
    
    action_calls = [
        {
            "function": "tiny_action",
            "kwargs": {
                "reasoning": reasoning_result,
                "agent_role": reasoning_calls[i]["kwargs"]["agent_role"]
            }
        }
        for i, reasoning_result in enumerate(reasoning_results)
    ]
    
    # Execute action generation concurrently
    action_results = await client.call_concurrent(action_calls)
    
    print("   ✓ Actions generated for all aspects")
    
    # Display pipeline results
    print("\n📊 Pipeline Results:")
    print("-" * 50)
    
    roles = ["system architect", "devops engineer", "security analyst"]
    for role, reasoning, action in zip(roles, reasoning_results, action_results):
        print(f"\n🤖 {role}:")
        print(f"   💭 Reasoning: {reasoning[:100]}...")
        print(f"   🎯 Action: {action[:100]}...")
    
    # Cleanup
    await client.close()


async def agent_selection_demo():
    """Demonstrate concurrent agent selection for multiple tasks."""
    print("\n" + "=" * 50)
    print("🎯 Agent Selection Demo")
    print("=" * 50)
    
    # Initialize client
    client = AsyncTensorZeroClient()
    await client.initialize()
    
    # Define tasks requiring agent selection
    tasks = [
        "Create a 5-year strategic vision",
        "Analyze customer churn data",
        "Build a project timeline",
        "Design system architecture",
        "Review code quality",
        "Optimize database queries"
    ]
    
    available_agents = ["strategist", "analyzer", "planner", "architect", "reviewer", "optimizer"]
    
    print(f"\n📋 Tasks to assign:")
    for i, task in enumerate(tasks, 1):
        print(f"   {i}. {task}")
    
    print(f"\n🤖 Available agents: {', '.join(available_agents)}")
    
    # Create selection calls
    selection_calls = [
        {
            "function": "agent_selection",
            "kwargs": {
                "task": task,
                "agents": available_agents
            }
        }
        for task in tasks
    ]
    
    print("\n⚡ Selecting optimal agents concurrently...")
    start_time = time.time()
    
    # Execute all selections concurrently
    selections = await client.call_concurrent(selection_calls)
    
    elapsed = time.time() - start_time
    
    print(f"   ✓ Completed in {elapsed:.2f} seconds")
    
    print("\n📊 Agent Assignments:")
    print("-" * 50)
    
    for task, selected_agent in zip(tasks, selections):
        print(f"   • {task}")
        print(f"     → Assigned to: {selected_agent}")
    
    # Cleanup
    await client.close()


async def performance_comparison():
    """Compare sequential vs concurrent execution performance."""
    print("\n" + "=" * 50)
    print("📊 Performance Comparison: Sequential vs Concurrent")
    print("=" * 50)
    
    # Initialize client
    client = AsyncTensorZeroClient()
    await client.initialize()
    
    # Create test calls
    num_calls = 10
    test_calls = [
        {
            "function": "tiny_reasoning",
            "kwargs": {
                "input_text": f"Analyze task {i}",
                "agent_role": "analyst"
            }
        }
        for i in range(num_calls)
    ]
    
    print(f"\n📋 Test: {num_calls} LLM calls")
    
    # Sequential execution
    print("\n1️⃣ Sequential Execution:")
    start_time = time.time()
    
    sequential_results = []
    for call in test_calls:
        result = await client.call(call["function"], **call["kwargs"])
        sequential_results.append(result)
    
    sequential_time = time.time() - start_time
    print(f"   Time: {sequential_time:.2f} seconds")
    print(f"   Rate: {num_calls/sequential_time:.2f} calls/second")
    
    # Concurrent execution
    print("\n2️⃣ Concurrent Execution:")
    start_time = time.time()
    
    concurrent_results = await client.call_concurrent(test_calls)
    
    concurrent_time = time.time() - start_time
    print(f"   Time: {concurrent_time:.2f} seconds")
    print(f"   Rate: {num_calls/concurrent_time:.2f} calls/second")
    
    # Calculate speedup
    speedup = sequential_time / concurrent_time
    print(f"\n🚀 Speedup: {speedup:.2f}x faster with concurrent execution!")
    
    # Verify results are consistent
    print(f"\n✅ Results consistency check: ", end="")
    if len(sequential_results) == len(concurrent_results):
        print("PASSED (same number of results)")
    else:
        print("FAILED (different result counts)")
    
    # Cleanup
    await client.close()


async def error_handling_demo():
    """Demonstrate error handling in concurrent calls."""
    print("\n" + "=" * 50)
    print("⚠️ Error Handling Demo")
    print("=" * 50)
    
    # Initialize client
    client = AsyncTensorZeroClient()
    await client.initialize()
    
    # Mix of valid and potentially problematic calls
    mixed_calls = [
        {
            "function": "tiny_reasoning",
            "kwargs": {
                "input_text": "Normal task",
                "agent_role": "analyst"
            }
        },
        {
            "function": "invalid_function",  # This will trigger fallback
            "kwargs": {
                "input_text": "This should fail gracefully"
            }
        },
        {
            "function": "tiny_action",
            "kwargs": {
                "reasoning": "Some reasoning",
                "agent_role": "planner"
            }
        }
    ]
    
    print("\n📋 Testing error resilience with mixed calls")
    print("   (Including an invalid function)")
    
    try:
        # Execute with error handling
        results = await client.call_concurrent(mixed_calls)
        
        print("\n✅ All calls completed (with fallbacks where needed)")
        print("\n📊 Results:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result[:100]}...")
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    # Cleanup
    await client.close()


async def main():
    """Run all TensorZero async examples."""
    
    print("""
╔════════════════════════════════════════════════════╗
║      Async TensorZero Integration Examples        ║
╚════════════════════════════════════════════════════╝
    """)
    
    # Run examples
    examples = [
        basic_concurrent_calls,
        reasoning_to_action_pipeline,
        agent_selection_demo,
        performance_comparison,
        error_handling_demo
    ]
    
    for example in examples:
        try:
            await example()
        except KeyboardInterrupt:
            print("\n⚠️ Example interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Example error: {e}")
            continue
        
        # Pause between examples
        if example != examples[-1]:
            print("\n" + "=" * 50)
            input("Press Enter to continue to next example...")
    
    print("""
╔════════════════════════════════════════════════════╗
║           Examples Complete! 🎉                   ║
║                                                    ║
║  Key Features Demonstrated:                       ║
║  • Concurrent LLM calls                           ║
║  • Reasoning-to-action pipelines                  ║
║  • Agent selection                                ║
║  • Performance optimization                       ║
║  • Error resilience                               ║
╚════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())