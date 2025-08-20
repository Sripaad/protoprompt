#!/usr/bin/env python3
"""
Async Multi-Agent Demo for TinyContext.

Demonstrates concurrent agent execution using the async infrastructure.
"""

import asyncio
import time
from typing import List, Dict, Any
from pathlib import Path
import sys

# 
# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tinycontext.agents.loader import TinyPerson
from tinycontext.core.react_loop import AsyncReActLoop
from tinycontext.inference.tensorzero_client import AsyncTensorZeroClient


# Create sample agents with different roles
def create_agents() -> List[TinyPerson]:
    """Create a team of specialized agents."""
    
    agents = []
    
    # Strategic Agent
    strategist = TinyPerson(
        name="Alice",
        role="strategist",
        persona="Expert in high-level strategic planning and vision setting",
        prompts={
            "system": "You are a strategic planning expert focused on big-picture thinking.",
            "reasoning_template": "As a strategist, analyze: {input}",
            "action_template": "Strategic action based on: {reasoning}"
        }
    )
    agents.append(strategist)
    
    # Data Analyst
    analyst = TinyPerson(
        name="Bob",
        role="analyzer",
        persona="Data-driven analyst specializing in metrics and insights",
        prompts={
            "system": "You are a data analyst who makes decisions based on evidence.",
            "reasoning_template": "From an analytical perspective: {input}",
            "action_template": "Data-driven action: {reasoning}"
        }
    )
    agents.append(analyst)
    
    # Project Planner
    planner = TinyPerson(
        name="Carol",
        role="planner",
        persona="Detail-oriented project planner focused on execution",
        prompts={
            "system": "You are a project planner who breaks down complex tasks.",
            "reasoning_template": "Planning approach for: {input}",
            "action_template": "Executable plan: {reasoning}"
        }
    )
    agents.append(planner)
    
    # Technical Expert
    technician = TinyPerson(
        name="Dave",
        role="technician",
        persona="Technical implementation expert and problem solver",
        prompts={
            "system": "You are a technical expert who designs and implements solutions.",
            "reasoning_template": "Technical analysis of: {input}",
            "action_template": "Technical solution: {reasoning}"
        }
    )
    agents.append(technician)
    
    return agents


async def concurrent_agent_demo():
    """
    Demonstrate concurrent agent execution.
    
    Multiple agents process the same task simultaneously,
    showcasing parallel thinking and diverse perspectives.
    """
    print("🚀 TinyContext Async Multi-Agent Demo")
    print("=" * 50)
    
    # Initialize async TensorZero client
    # Use HTTP gateway to connect to Docker services for proper observability
    client = AsyncTensorZeroClient(use_embedded=False)
    await client.initialize()
    
    # Initialize async ReAct loop
    react_loop = AsyncReActLoop(llm_client=client)
    
    # Create agents
    agents = create_agents()
    print(f"\n📋 Created {len(agents)} specialized agents:")
    for agent in agents:
        print(f"   • {agent.name} ({agent.role}): {agent.persona[:50]}...")
    
    # Define a complex task requiring multiple perspectives
    task = """
    We need to develop a new AI-powered customer service platform 
    that can handle 100,000+ daily interactions while maintaining 
    high satisfaction scores. Consider technical architecture, 
    strategic positioning, data requirements, and implementation timeline.
    """
    
    print(f"\n📝 Task: {task.strip()}")
    print("\n⚡ Executing concurrent agent reasoning...")
    print("-" * 50)
    
    # Prepare agent tasks
    agent_tasks = [
        (agent, task, {"request_id": f"req_{i}"})
        for i, agent in enumerate(agents)
    ]
    
    # Measure concurrent execution time
    start_time = time.time()
    
    # Execute all agents concurrently
    results = await react_loop.execute_concurrent_steps(agent_tasks)
    
    concurrent_time = time.time() - start_time
    
    # Display results
    print("\n📊 Concurrent Execution Results:")
    print("-" * 50)
    for agent, result in zip(agents, results):
        print(f"\n🤖 {agent.name} ({agent.role}):")
        print(f"   💭 Reasoning: {result.reasoning[:150]}...")
        print(f"   🎯 Action: {result.action[:150]}...")
        if result.metadata.get("handoff"):
            print(f"   🔄 Handoff to: {result.metadata['handoff']}")
    
    print(f"\n⏱️  Concurrent execution time: {concurrent_time:.2f} seconds")
    
    # Now demonstrate sequential execution for comparison
    print("\n" + "=" * 50)
    print("📊 Sequential Execution (for comparison):")
    print("-" * 50)
    
    start_time = time.time()
    sequential_results = []
    
    for agent, input_text, context in agent_tasks:
        result = await react_loop.execute_step(agent, input_text, context)
        sequential_results.append(result)
    
    sequential_time = time.time() - start_time
    
    print(f"⏱️  Sequential execution time: {sequential_time:.2f} seconds")
    print(f"🚀 Speedup: {sequential_time/concurrent_time:.2f}x faster with concurrent execution!")
    
    # Cleanup
    await client.close()


async def parallel_task_processing():
    """
    Demonstrate processing multiple different tasks in parallel.
    
    Different agents work on different tasks simultaneously.
    """
    print("\n" + "=" * 50)
    print("🔄 Parallel Task Processing Demo")
    print("=" * 50)
    
    # Initialize components
    # Use HTTP gateway for observability
    client = AsyncTensorZeroClient(use_embedded=False)
    await client.initialize()
    react_loop = AsyncReActLoop(llm_client=client)
    
    # Create agents
    agents = create_agents()
    
    # Define different tasks for different agents
    tasks = [
        ("Analyze market trends for AI adoption in healthcare", agents[1]),  # Analyst
        ("Create 6-month roadmap for product launch", agents[2]),           # Planner
        ("Design microservices architecture for scalability", agents[3]),   # Technician
        ("Develop competitive positioning strategy", agents[0]),            # Strategist
    ]
    
    print("\n📋 Parallel Tasks:")
    for i, (task, agent) in enumerate(tasks, 1):
        print(f"   {i}. [{agent.role}] {task}")
    
    # Prepare tasks for concurrent execution
    agent_tasks = [
        (agent, task, {"task_id": f"task_{i}"})
        for i, (task, agent) in enumerate(tasks)
    ]
    
    print("\n⚡ Processing all tasks concurrently...")
    start_time = time.time()
    
    # Execute all tasks in parallel
    results = await react_loop.execute_concurrent_steps(agent_tasks)
    
    elapsed = time.time() - start_time
    
    print("\n✅ All tasks completed!")
    print("-" * 50)
    
    for (task, agent), result in zip(tasks, results):
        print(f"\n📌 Task: {task[:60]}...")
        print(f"   Agent: {agent.name} ({agent.role})")
        print(f"   Result: {result.action[:100]}...")
    
    print(f"\n⏱️  Total processing time: {elapsed:.2f} seconds")
    print(f"   (All {len(tasks)} tasks processed in parallel)")
    
    # Cleanup
    await client.close()


async def agent_collaboration_demo():
    """
    Demonstrate agent collaboration through handoffs.
    
    Agents work together by handing off tasks to specialists.
    """
    print("\n" + "=" * 50)
    print("🤝 Agent Collaboration Demo")
    print("=" * 50)
    
    # Initialize components
    # Use HTTP gateway for observability
    client = AsyncTensorZeroClient(use_embedded=False)
    await client.initialize()
    react_loop = AsyncReActLoop(llm_client=client)
    
    # Create agents
    agents = create_agents()
    agent_map = {agent.role: agent for agent in agents}
    
    # Complex task requiring collaboration
    initial_task = """
    A Fortune 500 company wants to implement an AI transformation.
    Start with strategic assessment, then technical planning.
    """
    
    print(f"\n📝 Initial Task: {initial_task.strip()}")
    
    # Start with strategist
    current_agent = agent_map["strategist"]
    current_task = initial_task
    handoff_chain = []
    
    print("\n🔄 Starting collaboration chain...")
    print("-" * 50)
    
    for iteration in range(4):  # Max 4 handoffs
        print(f"\n📍 Step {iteration + 1}: {current_agent.name} ({current_agent.role})")
        
        # Execute current agent's step
        result = await react_loop.execute_step(
            current_agent, 
            current_task,
            {"iteration": iteration}
        )
        
        print(f"   Action: {result.action[:100]}...")
        
        handoff_chain.append({
            "agent": current_agent.name,
            "role": current_agent.role,
            "action": result.action
        })
        
        # Check for handoff
        if result.metadata.get("handoff"):
            next_role = result.metadata["handoff"]
            if next_role in agent_map:
                print(f"   → Handing off to: {next_role}")
                current_agent = agent_map[next_role]
                current_task = f"Continue from: {result.action[:100]}..."
            else:
                print(f"   ✓ Collaboration complete")
                break
        else:
            print(f"   ✓ Task complete")
            break
    
    print("\n📊 Collaboration Summary:")
    print("-" * 50)
    for i, step in enumerate(handoff_chain, 1):
        print(f"{i}. {step['agent']} ({step['role']})")
    
    # Cleanup
    await client.close()


async def stress_test_demo():
    """
    Stress test with many concurrent agents.
    
    Demonstrates system performance with high concurrency.
    """
    print("\n" + "=" * 50)
    print("🔥 Stress Test: High Concurrency Demo")
    print("=" * 50)
    
    # Initialize components
    # Use HTTP gateway for observability
    client = AsyncTensorZeroClient(use_embedded=False)
    await client.initialize()
    react_loop = AsyncReActLoop(llm_client=client)
    
    # Create many agent instances
    num_agents = 20
    agents = []
    
    base_agents = create_agents()
    for i in range(num_agents):
        base = base_agents[i % len(base_agents)]
        # Create variant with unique name
        agent = TinyPerson(
            name=f"{base.name}_{i}",
            role=base.role,
            persona=base.persona,
            prompts=base.prompts
        )
        agents.append(agent)
    
    print(f"\n🤖 Created {num_agents} agent instances")
    
    # Create varied tasks
    task_templates = [
        "Analyze the impact of {}",
        "Create a plan for {}",
        "Evaluate the risks of {}",
        "Design a solution for {}"
    ]
    
    topics = [
        "AI automation", "cloud migration", "data privacy",
        "remote work", "digital transformation"
    ]
    
    # Generate agent-task pairs
    agent_tasks = []
    for i, agent in enumerate(agents):
        template = task_templates[i % len(task_templates)]
        topic = topics[i % len(topics)]
        task = template.format(topic)
        agent_tasks.append((agent, task, {"task_id": i}))
    
    print(f"📋 Generated {len(agent_tasks)} tasks")
    print("\n⚡ Executing all tasks concurrently...")
    
    start_time = time.time()
    
    # Execute all tasks concurrently
    try:
        results = await react_loop.execute_concurrent_steps(agent_tasks)
        success = True
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        success = False
        results = []
    
    elapsed = time.time() - start_time
    
    if success:
        print(f"\n✅ Successfully processed {len(results)} tasks!")
        print(f"⏱️  Total time: {elapsed:.2f} seconds")
        print(f"📊 Average time per task: {elapsed/len(results):.3f} seconds")
        print(f"🚀 Throughput: {len(results)/elapsed:.1f} tasks/second")
    
    # Cleanup
    await client.close()


async def main():
    """Run all async demos."""
    
    print("""
╔════════════════════════════════════════════════════╗
║     TinyContext Async Multi-Agent System Demo     ║
╚════════════════════════════════════════════════════╝
    """)
    
    # Run demos in sequence
    demos = [
        concurrent_agent_demo,
        parallel_task_processing,
        agent_collaboration_demo,
        stress_test_demo
    ]
    
    for demo in demos:
        try:
            await demo()
        except KeyboardInterrupt:
            print("\n⚠️ Demo interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Demo error: {e}")
            continue
        
        # Pause between demos
        if demo != demos[-1]:
            print("\n" + "=" * 50)
            input("Press Enter to continue to next demo...")
    
    print("""
╔════════════════════════════════════════════════════╗
║              Demo Complete! 🎉                    ║
║                                                    ║
║  The async infrastructure enables:                ║
║  • Concurrent multi-agent reasoning               ║
║  • Parallel task processing                       ║
║  • Efficient agent collaboration                  ║
║  • High-throughput operations                     ║
╚════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())