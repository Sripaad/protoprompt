#!/usr/bin/env python3
"""
Research Assistant Example - Context Engineering Showcase

This example demonstrates context engineering patterns with a research assistant
that can:
1. Build persistent knowledge base (Write Context)
2. Retrieve relevant information (Select Context)  
3. Compress long research sessions (Compress Context)
4. Isolate different research topics (Isolate Context)

Usage:
    python examples/simple_research_assistant.py
"""

import asyncio
import json
from pathlib import Path
from tinycontext.simple import ContextAgent


async def research_session_demo():
    """Demonstrate a complete research session with context engineering"""
    print("🔬 Research Assistant - Context Engineering Demo")
    print("=" * 50)
    
    # Initialize research assistant
    assistant = ContextAgent(
        name="research_assistant",
        storage_path="./research_memory"
    )
    
    await assistant.initialize()
    
    # Phase 1: Build knowledge base (Write Context pattern)
    print("\n📚 Phase 1: Building Knowledge Base (Write Context)")
    research_topics = [
        {
            "topic": "quantum_computing", 
            "content": "Quantum computing uses quantum mechanical phenomena like superposition and entanglement to perform computations. Key players include IBM, Google, and Rigetti.",
            "tags": ["technology", "computing", "physics"]
        },
        {
            "topic": "climate_change",
            "content": "Climate change refers to long-term shifts in global temperatures and weather patterns. Primary causes include greenhouse gas emissions from human activities.",
            "tags": ["environment", "science", "policy"]
        },
        {
            "topic": "ai_safety",
            "content": "AI safety focuses on ensuring artificial intelligence systems are beneficial, reliable, and aligned with human values. Key concerns include alignment, robustness, and interpretability.",
            "tags": ["technology", "ai", "safety"]
        }
    ]
    
    for topic_data in research_topics:
        await assistant.add_context(
            topic_data["topic"],
            topic_data["content"], 
            topic_data["tags"],
            persistent=True
        )
        print(f"  ✓ Added knowledge: {topic_data['topic']}")
    
    # Phase 2: Research with context selection (Select Context pattern)
    print("\n🔍 Phase 2: Research with Context Selection (Select Context)")
    
    research_queries = [
        "What are the current developments in quantum computing?",
        "How does AI safety relate to quantum computing?", 
        "What environmental impacts might quantum computing have?"
    ]
    
    for i, query in enumerate(research_queries, 1):
        print(f"\n  Query {i}: {query}")
        
        result = await assistant.run(
            task=query,
            context_strategy="select",  # Use context selection
            max_iterations=1
        )
        
        print(f"  Answer: {result['output'][:200]}...")
        print(f"  Strategy: {result['context_strategy']}")
        
        # Simulate some delay between queries
        await asyncio.sleep(0.5)
    
    # Phase 3: Long research session with compression (Compress Context pattern)
    print("\n🗜️ Phase 3: Long Research Session (Compress Context)")
    
    # Simulate a long conversation
    long_queries = [
        "Summarize quantum computing basics",
        "What are quantum gates?",
        "Explain quantum entanglement",
        "How do quantum computers achieve speedup?",
        "What are the current limitations?",
        "When will quantum computers be practical?",
        "Create a research summary of our discussion"
    ]
    
    for i, query in enumerate(long_queries, 1):
        print(f"  Query {i}: {query[:50]}...")
        
        result = await assistant.run(
            task=query,
            context_strategy="compress",  # Use context compression
            max_iterations=1
        )
        
        print(f"    → {result['output'][:100]}...")
    
    # Get compressed conversation history
    history = await assistant.get_conversation_history(compressed=True)
    print(f"  Compressed history: {len(history)} messages (from original conversation)")
    
    # Phase 4: Isolated research contexts (Isolate Context pattern)
    print("\n🔒 Phase 4: Isolated Research Contexts (Isolate Context)")
    
    # Create isolated contexts for different research areas
    contexts = {
        "technical_analysis": {
            "focus": "technical aspects",
            "depth": "expert",
            "format": "detailed"
        },
        "business_analysis": {
            "focus": "commercial applications", 
            "depth": "executive",
            "format": "summary"
        },
        "policy_analysis": {
            "focus": "regulatory implications",
            "depth": "policy",
            "format": "recommendations"
        }
    }
    
    for context_name, schema in contexts.items():
        context_id = await assistant.create_isolated_context(context_name, schema)
        print(f"  ✓ Created isolated context: {context_name}")
        
        # Run analysis in isolated context
        result = await assistant.run(
            task=f"Analyze quantum computing from {schema['focus']} perspective",
            context_strategy="isolate",
            max_iterations=1
        )
        
        print(f"    → {result['output'][:150]}...")
    
    # Phase 5: Demonstrate context persistence
    print("\n💾 Phase 5: Context Persistence Demo")
    
    # Show persistent memories
    memories = await assistant.context_writer.list_memories()
    print(f"  Persistent memories stored: {len(memories)}")
    for memory in memories[:3]:  # Show first 3
        content = await assistant.context_writer.read_memory(memory)
        print(f"    - {memory}: {str(content)[:100]}...")
    
    # Final research synthesis
    print("\n🎯 Final: Research Synthesis")
    
    synthesis_result = await assistant.run(
        task="Create a comprehensive research report synthesizing all our previous discussions about quantum computing, AI safety, and climate change connections",
        context_strategy="auto",  # Use automatic context engineering
        max_iterations=2
    )
    
    print(f"\nFinal Report: {synthesis_result['output']}")
    print(f"\nContext Strategy Used: {synthesis_result['context_strategy']}")
    print(f"Framework: {synthesis_result['framework']}")
    
    return synthesis_result


async def interactive_research_mode():
    """Interactive mode for user queries"""
    print("\n🤖 Interactive Research Mode")
    print("Ask me anything! Type 'quit' to exit.")
    
    assistant = ContextAgent(name="interactive_researcher")
    await assistant.initialize()
    
    # Pre-load some context
    await assistant.add_context(
        "general_knowledge",
        "I am a research assistant with knowledge across multiple domains including technology, science, business, and policy.",
        ["general", "assistant"]
    )
    
    while True:
        try:
            query = input("\n🔍 Your question: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
                
            if not query:
                continue
            
            print("🤔 Researching...")
            result = await assistant.run(
                task=query,
                context_strategy="auto"
            )
            
            print(f"\n📝 Answer: {result['output']}")
            print(f"   Strategy: {result['context_strategy']}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main():
    """Main entry point"""
    print("TinyContext Research Assistant Demo")
    print("Choose mode:")
    print("1. Full demo (automated research session)")
    print("2. Interactive mode")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            await research_session_demo()
        elif choice == "2":
            await interactive_research_mode()
        else:
            print("Invalid choice. Running full demo...")
            await research_session_demo()
            
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have:")
        print("1. Set GROQ_API_KEY in your environment (preferred for speed)")
        print("2. Or set OPENAI_API_KEY as fallback")
        print("3. Installed dependencies: pip install tinycontext")


if __name__ == "__main__":
    asyncio.run(main())