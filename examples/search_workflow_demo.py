#!/usr/bin/env python3
"""
Search-enabled Workflow Demonstration.

This example shows how to integrate search capabilities into workflows
for research, information gathering, and decision-making tasks.
"""

import asyncio
import json
from pathlib import Path
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tinycontext.workflows.workflow_definition import (
    WorkflowBuilder,
    WorkflowDefinition,
    WorkflowNode,
    WorkflowNodeType
)
from tinycontext.workflows.workflow_executor import WorkflowExecutor, WorkflowExecutionContext
from tinycontext.manager.async_context_manager import AsyncTinyContextManager
from tinycontext.inference.tensorzero_client import AsyncTensorZeroClient


def create_research_workflow() -> WorkflowDefinition:
    """
    Create a research workflow that uses search capabilities.
    """
    builder = WorkflowBuilder("research_workflow_v1", "Research & Analysis Workflow")
    
    builder.with_description("Multi-stage research with search integration")
    builder.with_observability({
        "enabled": True,
        "trace_level": "debug",
        "metrics": {
            "search_queries": True,
            "search_results_quality": True,
            "research_depth": True,
            "synthesis_quality": True
        }
    })
    
    # Phase 1: Initial Query Analysis
    builder.add_agent_node(
        "query_analysis",
        "Query Analysis",
        agent_role="analyzer",
        prompt_template="Analyze research request and identify key topics: {input}"
    )
    
    # Phase 2: Parallel Search Operations
    builder.add_parallel_nodes(
        "search_phase",
        "Multi-Domain Search",
        ["web_search", "code_search", "academic_search"]
    )
    
    # Search nodes with different search types
    search_node = WorkflowNode(
        id="web_search",
        type=WorkflowNodeType.AGENT,
        name="Web Search",
        agent_role="searcher",
        config={
            "search_type": "web",
            "function": "tiny_search"
        }
    )
    builder.workflow.add_node(search_node)
    
    code_search_node = WorkflowNode(
        id="code_search",
        type=WorkflowNodeType.AGENT,
        name="Code Search",
        agent_role="searcher",
        config={
            "search_type": "code",
            "function": "tiny_search"
        }
    )
    builder.workflow.add_node(code_search_node)
    
    academic_search_node = WorkflowNode(
        id="academic_search",
        type=WorkflowNodeType.AGENT,
        name="Academic Search",
        agent_role="searcher",
        config={
            "search_type": "research",
            "function": "tiny_search"
        }
    )
    builder.workflow.add_node(academic_search_node)
    
    # Phase 3: Information Synthesis
    builder.add_agent_node(
        "synthesis",
        "Information Synthesis",
        agent_role="strategist",
        prompt_template="Synthesize search results into comprehensive analysis"
    )
    
    # Phase 4: Deep Dive Decision
    builder.add_decision_node(
        "deep_dive_check",
        "Need Deep Dive?",
        condition="requires_deep_dive",
        branches={
            "True": "deep_search",
            "False": "final_report"
        }
    )
    
    # Optional Deep Search
    builder.add_agent_node(
        "deep_search",
        "Deep Topic Search",
        agent_role="searcher",
        prompt_template="Conduct deep search on identified gaps: {synthesis_output}"
    )
    
    # Final Report Generation
    builder.add_agent_node(
        "final_report",
        "Final Report",
        agent_role="planner",
        prompt_template="Generate comprehensive research report with citations"
    )
    
    # Connect nodes
    builder.connect("query_analysis", "search_phase")
    builder.connect("web_search", "synthesis")
    builder.connect("code_search", "synthesis")
    builder.connect("academic_search", "synthesis")
    builder.connect("synthesis", "deep_dive_check")
    builder.connect("deep_search", "final_report")
    
    return builder.build()


def create_competitive_analysis_workflow() -> WorkflowDefinition:
    """
    Create a competitive analysis workflow using search.
    """
    builder = WorkflowBuilder("competitive_analysis_v1", "Competitive Analysis")
    
    builder.with_description("Market and competitor research workflow")
    
    # Market Overview
    builder.add_agent_node(
        "market_overview",
        "Market Overview",
        agent_role="analyzer",
        prompt_template="Analyze market segment: {market_segment}"
    )
    
    # Competitor Identification
    builder.add_agent_node(
        "competitor_search",
        "Competitor Search",
        agent_role="searcher",
        prompt_template="Search for competitors in {market_segment}"
    )
    
    # Parallel competitor analysis
    builder.add_parallel_nodes(
        "competitor_analysis",
        "Analyze Competitors",
        ["product_comparison", "pricing_analysis", "feature_analysis"]
    )
    
    builder.add_agent_node(
        "product_comparison",
        "Product Comparison",
        agent_role="analyzer",
        prompt_template="Compare competitor products"
    )
    
    builder.add_agent_node(
        "pricing_analysis",
        "Pricing Analysis",
        agent_role="analyzer",
        prompt_template="Analyze competitor pricing strategies"
    )
    
    builder.add_agent_node(
        "feature_analysis",
        "Feature Analysis",
        agent_role="analyzer",
        prompt_template="Compare feature sets across competitors"
    )
    
    # Strategic Recommendations
    builder.add_agent_node(
        "strategy_recommendations",
        "Strategic Recommendations",
        agent_role="strategist",
        prompt_template="Develop competitive strategy based on analysis"
    )
    
    # Connect workflow
    builder.connect("market_overview", "competitor_search")
    builder.connect("competitor_search", "competitor_analysis")
    builder.connect("product_comparison", "strategy_recommendations")
    builder.connect("pricing_analysis", "strategy_recommendations")
    builder.connect("feature_analysis", "strategy_recommendations")
    
    return builder.build()


class SearchWorkflowExecutor(WorkflowExecutor):
    """
    Extended workflow executor with search capabilities.
    """
    
    async def _execute_agent_node(
        self,
        node: WorkflowNode,
        context: WorkflowExecutionContext
    ) -> Any:
        """Execute an agent node, with special handling for search nodes."""
        
        # Check if this is a search node
        if node.config.get("function") == "tiny_search":
            return await self._execute_search_node(node, context)
        
        # Otherwise, use standard agent execution
        return await super()._execute_agent_node(node, context)
    
    async def _execute_search_node(
        self,
        node: WorkflowNode,
        context: WorkflowExecutionContext
    ) -> Any:
        """Execute a search node using TensorZero search function."""
        
        # Get search parameters from context
        query = context.get_variable("search_query", "")
        if not query:
            # Extract from input or previous outputs
            query = context.input_data.get("query", "")
            if not query:
                # Try to extract from previous node output
                prev_output = context.get_variable(f"{node.id}_input", "")
                query = str(prev_output)[:200] if prev_output else "general search"
        
        search_type = node.config.get("search_type", "general")
        search_context = context.get_variable("search_context", "")
        
        print(f"\n🔍 Executing search node: {node.name}")
        print(f"   Query: {query[:100]}...")
        print(f"   Type: {search_type}")
        
        # Call TensorZero search function
        try:
            search_result = await self.llm_client.call(
                "tiny_search",
                query=query,
                context=search_context,
                search_type=search_type
            )
            
            # Store search results in context
            context.set_variable(f"{node.id}_results", search_result)
            
            # Track search metrics
            context.set_variable(f"{node.id}_metrics", {
                "query_length": len(query),
                "search_type": search_type,
                "result_length": len(search_result),
                "timestamp": datetime.now().isoformat()
            })
            
            return search_result
            
        except Exception as e:
            print(f"   ⚠️ Search failed: {e}")
            return f"Search failed for query: {query}"


async def demonstrate_search_workflows():
    """
    Demonstrate search-enabled workflows.
    """
    print("=" * 70)
    print("🔍 TinyContext Search-Enabled Workflows Demo")
    print("=" * 70)
    
    # Initialize components
    print("\n📦 Initializing components...")
    llm_client = AsyncTensorZeroClient(use_embedded=False)
    await llm_client.initialize()
    
    context_manager = AsyncTinyContextManager(llm_client=llm_client)
    await context_manager.initialize()
    
    # Use extended executor with search capabilities
    executor = SearchWorkflowExecutor(
        context_manager=context_manager,
        llm_client=llm_client
    )
    
    print("✅ Components initialized with search capabilities")
    
    # Test 1: Research Workflow
    print("\n" + "=" * 70)
    print("📚 Test 1: Research Workflow with Multi-Domain Search")
    print("=" * 70)
    
    research_workflow = create_research_workflow()
    
    research_input = {
        "query": "Latest advances in transformer architectures for LLMs",
        "depth": "comprehensive",
        "domains": ["academic", "technical", "industry"],
        "timeframe": "2023-2025"
    }
    
    print(f"\n📥 Research Input:")
    print(json.dumps(research_input, indent=2))
    
    print(f"\n⚡ Starting research workflow...")
    
    try:
        research_context = await executor.execute(
            research_workflow,
            research_input
        )
        
        print(f"\n✅ Research workflow completed!")
        print(f"   Execution ID: {research_context.execution_id}")
        print(f"   Duration: {research_context.total_duration_ms:.2f}ms")
        
        # Display search results
        print(f"\n🔍 Search Results Summary:")
        for node_id in ["web_search", "code_search", "academic_search"]:
            if f"{node_id}_results" in research_context.variables:
                results = research_context.variables[f"{node_id}_results"]
                print(f"   {node_id}: {len(str(results))} chars")
                if f"{node_id}_metrics" in research_context.variables:
                    metrics = research_context.variables[f"{node_id}_metrics"]
                    print(f"      Type: {metrics['search_type']}")
        
        # Display synthesis
        if "synthesis_output" in research_context.variables:
            synthesis = research_context.variables["synthesis_output"]
            print(f"\n📊 Synthesis Preview:")
            print(f"   {str(synthesis)[:200]}...")
        
    except Exception as e:
        print(f"\n❌ Research workflow failed: {e}")
    
    # Test 2: Competitive Analysis
    print("\n" + "=" * 70)
    print("💼 Test 2: Competitive Analysis with Market Search")
    print("=" * 70)
    
    competitive_workflow = create_competitive_analysis_workflow()
    
    competitive_input = {
        "market_segment": "AI-powered code assistants",
        "company": "TinyContext AI",
        "competitors": ["GitHub Copilot", "Cursor", "Codeium"],
        "analysis_depth": "detailed"
    }
    
    print(f"\n📥 Competitive Analysis Input:")
    print(json.dumps(competitive_input, indent=2))
    
    print(f"\n⚡ Starting competitive analysis...")
    
    try:
        competitive_context = await executor.execute(
            competitive_workflow,
            competitive_input
        )
        
        print(f"\n✅ Competitive analysis completed!")
        print(f"   Duration: {competitive_context.total_duration_ms:.2f}ms")
        
        # Display competitor insights
        if "competitor_search_output" in competitive_context.variables:
            competitors = competitive_context.variables["competitor_search_output"]
            print(f"\n🏢 Competitors Analyzed:")
            print(f"   {str(competitors)[:300]}...")
        
        # Display recommendations
        if "strategy_recommendations_output" in competitive_context.variables:
            recommendations = competitive_context.variables["strategy_recommendations_output"]
            print(f"\n💡 Strategic Recommendations:")
            print(f"   {str(recommendations)[:300]}...")
        
    except Exception as e:
        print(f"\n❌ Competitive analysis failed: {e}")
    
    # Test 3: Dynamic Search Pipeline
    print("\n" + "=" * 70)
    print("🔄 Test 3: Dynamic Search Pipeline")
    print("=" * 70)
    
    # Create a simple dynamic search workflow
    builder = WorkflowBuilder("dynamic_search_v1", "Dynamic Search")
    
    # Initial search
    builder.add_agent_node(
        "initial_search",
        "Initial Search",
        agent_role="searcher",
        prompt_template="Search for: {query}"
    )
    
    # Refine search based on results
    builder.add_agent_node(
        "refine_query",
        "Refine Query",
        agent_role="analyzer",
        prompt_template="Refine search based on initial results"
    )
    
    # Follow-up search
    builder.add_agent_node(
        "followup_search",
        "Follow-up Search",
        agent_role="searcher",
        prompt_template="Deep search with refined query"
    )
    
    # Final analysis
    builder.add_agent_node(
        "final_analysis",
        "Final Analysis",
        agent_role="strategist",
        prompt_template="Analyze all search results"
    )
    
    builder.connect("initial_search", "refine_query")
    builder.connect("refine_query", "followup_search")
    builder.connect("followup_search", "final_analysis")
    
    dynamic_workflow = builder.build()
    
    dynamic_input = {
        "query": "Best practices for async Python with observability",
        "refinement_strategy": "iterative",
        "max_depth": 3
    }
    
    print(f"\n📥 Dynamic Search Input:")
    print(json.dumps(dynamic_input, indent=2))
    
    print(f"\n⚡ Starting dynamic search pipeline...")
    
    try:
        dynamic_context = await executor.execute(
            dynamic_workflow,
            dynamic_input
        )
        
        print(f"\n✅ Dynamic search completed!")
        print(f"   Total searches: {len([k for k in dynamic_context.variables if 'search' in k])}")
        print(f"   Duration: {dynamic_context.total_duration_ms:.2f}ms")
        
    except Exception as e:
        print(f"\n❌ Dynamic search failed: {e}")
    
    # Display search statistics
    print("\n" + "=" * 70)
    print("📊 Search Workflow Statistics")
    print("=" * 70)
    
    summary = executor.get_execution_summary()
    print(f"\n   Total Workflows Executed: {summary['completed_executions']}")
    print(f"   Active Executions: {summary['active_executions']}")
    
    # Calculate search-specific metrics
    total_searches = 0
    search_types_used = set()
    
    for context in executor.completed_executions:
        for key in context.variables:
            if "_metrics" in key and "search" in key:
                metrics = context.variables[key]
                if "search_type" in metrics:
                    search_types_used.add(metrics["search_type"])
                    total_searches += 1
    
    print(f"   Total Search Operations: {total_searches}")
    print(f"   Search Types Used: {', '.join(search_types_used)}")
    
    print("\n" + "=" * 70)
    print("✨ Search Workflow Demo Complete!")
    print("=" * 70)
    print("\n💡 Key Capabilities Demonstrated:")
    print("   • Multi-domain parallel search")
    print("   • Search type specialization (web, code, research)")
    print("   • Dynamic query refinement")
    print("   • Search result synthesis")
    print("   • Integrated observability")
    
    # Cleanup
    await context_manager.cleanup()
    await llm_client.close()


async def demonstrate_search_api():
    """
    Direct demonstration of search API capabilities.
    """
    print("\n" + "=" * 70)
    print("🔬 Direct Search API Demonstration")
    print("=" * 70)
    
    llm_client = AsyncTensorZeroClient(use_embedded=False)
    await llm_client.initialize()
    
    # Test different search types
    search_tests = [
        {
            "type": "web",
            "query": "TensorZero observability features",
            "context": "Looking for monitoring and tracing capabilities"
        },
        {
            "type": "code",
            "query": "async Python workflow orchestration",
            "context": "Need examples of FSM-based agent systems"
        },
        {
            "type": "research",
            "query": "Multi-agent systems with LLM integration",
            "context": "Academic papers and industry applications"
        },
        {
            "type": "general",
            "query": "Best practices for prompt engineering",
            "context": "For production LLM applications"
        }
    ]
    
    print("\n🧪 Testing Search Functions:")
    
    for test in search_tests:
        print(f"\n📍 Search Type: {test['type']}")
        print(f"   Query: {test['query']}")
        print(f"   Context: {test['context']}")
        
        try:
            result = await llm_client.call(
                "tiny_search",
                query=test["query"],
                context=test["context"],
                search_type=test["type"]
            )
            
            print(f"   ✅ Result preview:")
            print(f"      {result[:200]}...")
            
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
    
    await llm_client.close()


async def main():
    """
    Main demo function.
    """
    print("""
╔════════════════════════════════════════════════════════════════════╗
║       TinyContext Search Integration & Workflow Demo              ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run search workflow demonstrations
    await demonstrate_search_workflows()
    
    # Run direct API demonstration
    await demonstrate_search_api()
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                    Search Integration Complete! 🎉                ║
║                                                                    ║
║  Search capabilities integrated:                                  ║
║  • Web search for current information                             ║
║  • Code search for technical examples                             ║
║  • Research search for academic content                           ║
║  • General search for broad queries                               ║
║                                                                    ║
║  Workflow integration features:                                   ║
║  • Search nodes in workflow definitions                           ║
║  • Parallel multi-domain searches                                 ║
║  • Dynamic query refinement                                       ║
║  • Result synthesis and analysis                                  ║
║  • Full observability through TensorZero                          ║
╚════════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    asyncio.run(main())