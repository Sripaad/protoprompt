#!/usr/bin/env python3
"""
Fluid Agentic RAG - Dynamic Research Workflows

This demo shows how TinyContext agents can fluidly create research workflows:
- Simple questions → Single agent response
- Complex research → Multi-agent orchestration  
- Automatic workflow generation based on query complexity
- Real-time streaming with context engineering

The system decides whether to use:
1. Direct answer (simple questions)
2. Research pipeline (fact-finding)
3. Multi-perspective analysis (complex topics)
4. Iterative refinement (deep research)

Usage:
    python examples/fluid_agentic_rag.py
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from tinycontext.simple import ContextAgent


class FluidRAGSystem:
    """Intelligent RAG system that adapts workflow to query complexity"""
    
    def __init__(self):
        self.query_analyzer = None
        self.research_agents = {}
        self.knowledge_base = {}
        
    async def initialize(self):
        """Initialize the fluid RAG system"""
        print("🧠 Initializing Fluid Agentic RAG System...")
        
        # Create query analyzer that decides workflow
        self.query_analyzer = ContextAgent(
            name="rag_analyzer",
            storage_path="./rag_memory"
        )
        await self.query_analyzer.initialize()
        
        # Load RAG patterns and strategies
        await self._load_rag_patterns()
        
        print("✅ Fluid RAG System Ready!")
    
    async def _load_rag_patterns(self):
        """Load different RAG workflow patterns"""
        rag_patterns = {
            "direct_answer": {
                "description": "Single agent provides direct answer from existing knowledge",
                "complexity": "simple",
                "agents_needed": 1,
                "example": "What is the capital of France?"
            },
            "research_pipeline": {
                "description": "Sequential research: search → extract → synthesize",
                "complexity": "moderate", 
                "agents_needed": 3,
                "example": "How does machine learning work?"
            },
            "multi_perspective": {
                "description": "Multiple agents research different aspects in parallel",
                "complexity": "complex",
                "agents_needed": 4,
                "example": "What are the implications of AI on society?"
            },
            "iterative_deep_dive": {
                "description": "Iterative research with follow-up questions and refinement",
                "complexity": "expert",
                "agents_needed": 5,
                "example": "Analyze the economic impact of quantum computing on financial markets"
            }
        }
        
        for pattern_name, pattern_info in rag_patterns.items():
            await self.query_analyzer.add_context(
                f"rag_pattern_{pattern_name}",
                json.dumps(pattern_info),
                ["rag", "pattern", pattern_info["complexity"]],
                persistent=True
            )
        
        print(f"📚 Loaded {len(rag_patterns)} RAG patterns")
    
    async def answer_query(self, query: str, verbose: bool = True) -> Dict[str, Any]:
        """Automatically determine and execute appropriate RAG workflow"""
        if verbose:
            print(f"\n🔍 Query: {query}")
        
        start_time = time.time()
        
        # Step 1: Analyze query complexity and choose workflow
        workflow_decision = await self._analyze_query_complexity(query)
        
        if verbose:
            print(f"🎯 Strategy: {workflow_decision['pattern']} ({workflow_decision['complexity']})")
            print(f"👥 Agents needed: {workflow_decision['agents_needed']}")
        
        # Step 2: Execute appropriate workflow
        if workflow_decision['pattern'] == 'direct_answer':
            result = await self._direct_answer(query, verbose)
        elif workflow_decision['pattern'] == 'research_pipeline':
            result = await self._research_pipeline(query, verbose)
        elif workflow_decision['pattern'] == 'multi_perspective':
            result = await self._multi_perspective_research(query, verbose)
        else:  # iterative_deep_dive
            result = await self._iterative_deep_dive(query, verbose)
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "query": query,
            "strategy": workflow_decision['pattern'],
            "complexity": workflow_decision['complexity'],
            "agents_used": result.get("agents_used", []),
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.5),
            "duration_seconds": duration,
            "workflow_steps": result.get("steps", [])
        }
    
    async def _analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """Analyze query and determine optimal RAG workflow"""
        analysis_prompt = f"""
        Analyze this query and determine the optimal RAG workflow:
        Query: {query}
        
        Consider:
        1. Is this a simple factual question? → direct_answer
        2. Does it need research from multiple sources? → research_pipeline
        3. Does it need multiple perspectives/domains? → multi_perspective
        4. Is it a complex analysis requiring deep research? → iterative_deep_dive
        
        Respond with JSON:
        {{
            "pattern": "direct_answer|research_pipeline|multi_perspective|iterative_deep_dive",
            "complexity": "simple|moderate|complex|expert",
            "agents_needed": number,
            "reasoning": "why this pattern fits"
        }}
        """
        
        result = await self.query_analyzer.run(
            analysis_prompt,
            context_strategy="select"
        )
        
        try:
            import re
            json_match = re.search(r'\{.*\}', result["output"], re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
            else:
                # Default to research pipeline
                decision = {
                    "pattern": "research_pipeline",
                    "complexity": "moderate", 
                    "agents_needed": 3,
                    "reasoning": "Default research workflow"
                }
            return decision
        except:
            # Fallback
            return {
                "pattern": "direct_answer",
                "complexity": "simple",
                "agents_needed": 1, 
                "reasoning": "Fallback to simple response"
            }
    
    async def _direct_answer(self, query: str, verbose: bool) -> Dict[str, Any]:
        """Simple direct answer - single agent"""
        if verbose:
            print("  💡 Direct answer mode")
        
        agent = await self._get_agent("knowledge_expert")
        
        result = await agent.run(
            f"Provide a direct, helpful answer to: {query}",
            context_strategy="select"
        )
        
        return {
            "answer": result["output"],
            "agents_used": ["knowledge_expert"],
            "sources": ["internal_knowledge"],
            "confidence": 0.8,
            "steps": ["direct_response"]
        }
    
    async def _research_pipeline(self, query: str, verbose: bool) -> Dict[str, Any]:
        """Sequential research pipeline"""
        if verbose:
            print("  🔄 Research pipeline: search → extract → synthesize")
        
        steps = []
        
        # Step 1: Search for information
        searcher = await self._get_agent("researcher") 
        search_result = await searcher.run(
            f"Search for comprehensive information about: {query}",
            context_strategy="auto"
        )
        steps.append("search")
        if verbose:
            print(f"    🔍 Search: {search_result['output'][:100]}...")
        
        # Step 2: Extract key information
        extractor = await self._get_agent("extractor")
        extract_result = await extractor.run(
            f"Extract key information relevant to '{query}' from this research: {search_result['output']}",
            context_strategy="compress"
        )
        steps.append("extract")
        if verbose:
            print(f"    📋 Extract: {extract_result['output'][:100]}...")
        
        # Step 3: Synthesize answer
        synthesizer = await self._get_agent("synthesizer")
        final_result = await synthesizer.run(
            f"Create a comprehensive answer to '{query}' based on this extracted information: {extract_result['output']}",
            context_strategy="auto"
        )
        steps.append("synthesize")
        if verbose:
            print(f"    🎯 Synthesize: {final_result['output'][:100]}...")
        
        return {
            "answer": final_result["output"],
            "agents_used": ["researcher", "extractor", "synthesizer"],
            "sources": ["search_results", "extracted_facts"],
            "confidence": 0.85,
            "steps": steps
        }
    
    async def _multi_perspective_research(self, query: str, verbose: bool) -> Dict[str, Any]:
        """Multiple agents research different perspectives in parallel"""
        if verbose:
            print("  👥 Multi-perspective research (parallel)")
        
        # Define different research perspectives
        perspectives = {
            "technical": f"Research the technical aspects of: {query}",
            "practical": f"Research the practical applications of: {query}",
            "social": f"Research the social/ethical implications of: {query}",
            "economic": f"Research the economic impact of: {query}"
        }
        
        # Research perspectives in parallel
        research_results = {}
        tasks = []
        
        for perspective, research_task in perspectives.items():
            agent = await self._get_agent(f"{perspective}_researcher")
            task_coro = agent.run(research_task, context_strategy="auto")
            tasks.append((perspective, task_coro))
        
        # Execute research in parallel
        for perspective, task_coro in tasks:
            result = await task_coro
            research_results[perspective] = result["output"]
            if verbose:
                print(f"    🔬 {perspective}: {result['output'][:80]}...")
        
        # Synthesize all perspectives
        synthesizer = await self._get_agent("meta_synthesizer")
        synthesis_task = f"""
        Create a comprehensive answer to: {query}
        
        Based on these research perspectives:
        {json.dumps(research_results, indent=2)}
        
        Provide a balanced, multi-faceted answer that incorporates all perspectives.
        """
        
        final_result = await synthesizer.run(synthesis_task, context_strategy="compress")
        
        return {
            "answer": final_result["output"],
            "agents_used": list(perspectives.keys()) + ["meta_synthesizer"],
            "sources": list(perspectives.keys()),
            "confidence": 0.9,
            "steps": ["parallel_research", "synthesis"]
        }
    
    async def _iterative_deep_dive(self, query: str, verbose: bool) -> Dict[str, Any]:
        """Deep iterative research with follow-up questions"""
        if verbose:
            print("  🔄 Iterative deep dive research")
        
        # Initial research
        researcher = await self._get_agent("deep_researcher")
        initial_research = await researcher.run(
            f"Conduct initial research on: {query}. Identify key areas that need deeper investigation.",
            context_strategy="auto"
        )
        
        # Generate follow-up questions
        question_generator = await self._get_agent("question_generator")
        follow_ups = await question_generator.run(
            f"Based on this initial research about '{query}', generate 3 specific follow-up questions for deeper investigation: {initial_research['output']}",
            context_strategy="select"
        )
        
        if verbose:
            print(f"    🔍 Initial: {initial_research['output'][:80]}...")
            print(f"    ❓ Follow-ups: {follow_ups['output'][:80]}...")
        
        # Deep research on follow-ups
        deep_researcher = await self._get_agent("specialist_researcher")
        deep_research = await deep_researcher.run(
            f"Conduct deep research to answer these follow-up questions about '{query}': {follow_ups['output']}",
            context_strategy="compress"
        )
        
        # Final synthesis
        expert_synthesizer = await self._get_agent("expert_synthesizer")
        final_answer = await expert_synthesizer.run(
            f"Create an expert-level comprehensive answer to '{query}' integrating: Initial research: {initial_research['output']} Deep research: {deep_research['output']}",
            context_strategy="auto"
        )
        
        return {
            "answer": final_answer["output"],
            "agents_used": ["deep_researcher", "question_generator", "specialist_researcher", "expert_synthesizer"],
            "sources": ["initial_research", "follow_up_investigation", "deep_analysis"],
            "confidence": 0.95,
            "steps": ["initial_research", "follow_up_generation", "deep_research", "expert_synthesis"]
        }
    
    async def _get_agent(self, role: str) -> ContextAgent:
        """Get or create specialized research agent"""
        if role not in self.research_agents:
            self.research_agents[role] = ContextAgent(
                name=f"rag_{role}",
                storage_path=f"./rag_memory/{role}"
            )
            await self.research_agents[role].initialize()
            
            # Add role-specific expertise
            expertise = self._get_agent_expertise(role)
            await self.research_agents[role].add_context(
                f"{role}_expertise",
                expertise,
                [role, "expertise", "rag"],
                persistent=True
            )
        
        return self.research_agents[role]
    
    def _get_agent_expertise(self, role: str) -> str:
        """Define expertise for different research agent roles"""
        expertise_map = {
            "knowledge_expert": "Expert at providing accurate, direct answers from existing knowledge",
            "researcher": "Skilled at finding and gathering information from multiple sources", 
            "extractor": "Expert at extracting key facts and relevant details from research",
            "synthesizer": "Specialized in combining information into coherent, comprehensive answers",
            "technical_researcher": "Focused on technical and scientific aspects",
            "practical_researcher": "Focused on real-world applications and use cases",
            "social_researcher": "Focused on social, ethical, and cultural implications",
            "economic_researcher": "Focused on economic impacts and financial considerations",
            "meta_synthesizer": "Expert at synthesizing multiple perspectives into balanced answers",
            "deep_researcher": "Conducts thorough, detailed research on complex topics",
            "question_generator": "Expert at identifying gaps and generating follow-up research questions",
            "specialist_researcher": "Conducts specialized, expert-level research",
            "expert_synthesizer": "Creates expert-level comprehensive analyses"
        }
        
        return expertise_map.get(role, f"Expert {role} specializing in research and analysis")


async def demonstrate_fluid_rag():
    """Demonstrate fluid RAG with queries of different complexity"""
    print("🧠 Fluid Agentic RAG Demo")
    print("=" * 40)
    print("Watch how the system automatically chooses optimal research workflows!")
    
    rag_system = FluidRAGSystem()
    await rag_system.initialize()
    
    # Test queries of different complexity levels
    test_queries = [
        {
            "query": "What is Python?",
            "expected": "direct_answer",
            "description": "Simple factual question"
        },
        {
            "query": "How does machine learning actually work under the hood?", 
            "expected": "research_pipeline",
            "description": "Moderate research needed"
        },
        {
            "query": "What are the long-term implications of AI on employment, society, and governance?",
            "expected": "multi_perspective", 
            "description": "Complex multi-faceted analysis"
        },
        {
            "query": "Analyze how quantum computing will transform cryptography, financial systems, and global security over the next 20 years",
            "expected": "iterative_deep_dive",
            "description": "Expert-level deep analysis"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"🎯 RAG Demo {i}: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        print('='*60)
        
        try:
            result = await rag_system.answer_query(test_case["query"], verbose=True)
            
            print(f"\n📊 Results:")
            print(f"   Strategy Used: {result['strategy']}")
            print(f"   Complexity: {result['complexity']}")
            print(f"   Agents: {', '.join(result['agents_used'])}")
            print(f"   Duration: {result['duration_seconds']:.2f}s")
            print(f"   Confidence: {result['confidence']:.0%}")
            print(f"   Steps: {' → '.join(result['workflow_steps'])}")
            print(f"\n📝 Answer: {result['answer'][:300]}...")
            
        except Exception as e:
            print(f"❌ Demo {i} failed: {e}")
        
        # Brief pause between demos
        await asyncio.sleep(1)


async def interactive_rag():
    """Interactive RAG mode - ask any question"""
    print("\n🧠 Interactive Fluid RAG")
    print("Ask any question and watch adaptive research workflows emerge!")
    print("Type 'quit' to exit.\n")
    
    rag_system = FluidRAGSystem()
    await rag_system.initialize()
    
    while True:
        try:
            query = input("🔍 Your research question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            print(f"\n🧠 Analyzing query complexity...")
            result = await rag_system.answer_query(query, verbose=True)
            
            print(f"\n✅ Research Complete!")
            print(f"🎯 Strategy: {result['strategy']}")
            print(f"👥 Team: {', '.join(result['agents_used'])}")
            print(f"⏱️  Time: {result['duration_seconds']:.1f}s")
            print(f"🎯 Confidence: {result['confidence']:.0%}")
            print(f"\n📋 Answer: {result['answer']}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main():
    """Main entry point"""
    print("TinyContext Fluid Agentic RAG")
    print("Adaptive research workflows that match query complexity")
    print("\nChoose mode:")
    print("1. Automated demo (4 complexity levels)")
    print("2. Interactive mode (ask your own questions)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            await demonstrate_fluid_rag()
        elif choice == "2":
            await interactive_rag()
        else:
            print("Invalid choice. Running demo...")
            await demonstrate_fluid_rag()
            
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have:")
        print("1. Set GROQ_API_KEY in your environment")
        print("2. TinyContext properly configured")


if __name__ == "__main__":
    asyncio.run(main())