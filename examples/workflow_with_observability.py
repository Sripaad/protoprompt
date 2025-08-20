#!/usr/bin/env python3
"""
Comprehensive example demonstrating workflow execution with full observability.

This example shows how to:
1. Define complex multi-agent workflows
2. Execute them with full observability
3. Track metrics through TensorZero
4. Visualize execution in the TensorZero UI
"""

import asyncio
import json
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tinycontext.workflows.workflow_definition import (
    WorkflowBuilder,
    WorkflowDefinition,
    create_customer_service_workflow,
    create_data_analysis_workflow
)
from tinycontext.workflows.workflow_executor import WorkflowExecutor
from tinycontext.manager.async_context_manager import AsyncTinyContextManager
from tinycontext.inference.tensorzero_client import AsyncTensorZeroClient


def create_product_launch_workflow() -> WorkflowDefinition:
    """
    Create a complex product launch workflow with multiple agents.
    """
    builder = WorkflowBuilder("product_launch_v1", "Product Launch Workflow")
    
    builder.with_description("Comprehensive product launch planning and execution")
    builder.with_observability({
        "enabled": True,
        "trace_level": "debug",
        "metrics": {
            "workflow_duration": True,
            "node_durations": True,
            "token_usage": True,
            "agent_handoffs": True,
            "decision_points": True
        }
    })
    
    # Phase 1: Market Analysis
    builder.add_agent_node(
        "market_analysis",
        "Market Analysis",
        agent_role="analyzer",
        prompt_template="Analyze market conditions for product launch: {input}"
    )
    
    # Decision: Market readiness
    builder.add_decision_node(
        "market_readiness_check",
        "Check Market Readiness",
        condition="market_score > 7",  # Simplified condition
        branches={
            "True": "strategy_planning",
            "False": "market_preparation"
        }
    )
    
    # Branch: Additional market preparation
    builder.add_agent_node(
        "market_preparation",
        "Market Preparation",
        agent_role="strategist",
        prompt_template="Develop market preparation strategy: {market_analysis_output}"
    )
    
    # Phase 2: Strategic Planning (parallel)
    builder.add_parallel_nodes(
        "strategy_planning",
        "Strategic Planning",
        ["marketing_strategy", "technical_planning", "resource_planning"]
    )
    
    builder.add_agent_node(
        "marketing_strategy",
        "Marketing Strategy",
        agent_role="strategist",
        prompt_template="Develop marketing strategy for product launch"
    )
    
    builder.add_agent_node(
        "technical_planning",
        "Technical Planning",
        agent_role="planner",
        prompt_template="Create technical implementation plan"
    )
    
    builder.add_agent_node(
        "resource_planning",
        "Resource Planning",
        agent_role="planner",
        prompt_template="Plan resource allocation and timeline"
    )
    
    # Phase 3: Synthesis and Execution Plan
    builder.add_agent_node(
        "synthesis",
        "Plan Synthesis",
        agent_role="strategist",
        prompt_template="Synthesize all plans into comprehensive launch strategy"
    )
    
    # Connect nodes
    builder.connect("market_preparation", "strategy_planning")
    builder.connect("marketing_strategy", "synthesis")
    builder.connect("technical_planning", "synthesis")
    builder.connect("resource_planning", "synthesis")
    
    # Phase 4: Final Review
    builder.add_agent_node(
        "final_review",
        "Final Review",
        agent_role="analyzer",
        prompt_template="Review and validate complete launch plan"
    )
    
    builder.connect("synthesis", "final_review")
    
    return builder.build()


async def demonstrate_workflow_execution():
    """
    Demonstrate workflow execution with observability.
    """
    print("=" * 70)
    print("🚀 TinyContext Workflow Execution with Observability Demo")
    print("=" * 70)
    
    # Initialize components
    print("\n📦 Initializing components...")
    llm_client = AsyncTensorZeroClient(use_embedded=False)  # Use HTTP gateway
    await llm_client.initialize()
    
    context_manager = AsyncTinyContextManager(llm_client=llm_client)
    await context_manager.initialize()
    
    executor = WorkflowExecutor(
        context_manager=context_manager,
        llm_client=llm_client
    )
    
    print("✅ Components initialized")
    print(f"   - TensorZero Gateway: http://localhost:3000")
    print(f"   - TensorZero UI: http://localhost:4000")
    
    # Create workflows
    workflows = {
        "product_launch": create_product_launch_workflow(),
        "customer_service": create_customer_service_workflow(),
        "data_analysis": create_data_analysis_workflow()
    }
    
    print(f"\n📋 Available Workflows:")
    for name, workflow in workflows.items():
        print(f"   - {workflow.name} (v{workflow.version})")
        print(f"     {workflow.description}")
        errors = workflow.validate()
        if errors:
            print(f"     ⚠️ Validation errors: {errors}")
        else:
            print(f"     ✓ Valid workflow with {len(workflow.nodes)} nodes")
    
    # Execute product launch workflow
    print("\n" + "=" * 70)
    print("🎯 Executing Product Launch Workflow")
    print("=" * 70)
    
    input_data = {
        "product_name": "AI Assistant Pro",
        "target_market": "Enterprise customers",
        "launch_date": "Q2 2025",
        "budget": "$5M",
        "requirements": [
            "Scalable infrastructure",
            "24/7 support",
            "Multi-language support",
            "Security compliance"
        ]
    }
    
    print(f"\n📥 Input Data:")
    print(json.dumps(input_data, indent=2))
    
    print(f"\n⚡ Starting execution...")
    start_time = datetime.now()
    
    try:
        # Execute workflow
        context = await executor.execute(
            workflows["product_launch"],
            input_data
        )
        
        # Display results
        print(f"\n✅ Workflow completed successfully!")
        print(f"   Execution ID: {context.execution_id}")
        print(f"   Duration: {context.total_duration_ms:.2f}ms")
        print(f"   Status: {context.status}")
        
        print(f"\n📊 Execution Metrics:")
        trace = context.to_observability_trace()
        metrics = trace["metrics"]
        print(f"   - Total Nodes: {metrics['total_nodes']}")
        print(f"   - Successful: {metrics['successful_nodes']}")
        print(f"   - Failed: {metrics['failed_nodes']}")
        print(f"   - Avg Duration: {metrics['avg_node_duration_ms']:.2f}ms")
        
        print(f"\n🔍 Node Execution Details:")
        for node_result in context.node_results.values():
            status_icon = "✅" if node_result.status.value == "completed" else "❌"
            print(f"   {status_icon} {node_result.node_id}: {node_result.duration_ms:.2f}ms")
            if node_result.output:
                output_preview = str(node_result.output)[:100]
                print(f"      Output: {output_preview}...")
        
        print(f"\n📝 Final Variables:")
        for key, value in context.variables.items():
            if not key.endswith("_output"):  # Skip output variables for brevity
                print(f"   - {key}: {value}")
        
    except Exception as e:
        print(f"\n❌ Workflow execution failed: {e}")
    
    # Execute multiple workflows concurrently
    print("\n" + "=" * 70)
    print("🔄 Executing Multiple Workflows Concurrently")
    print("=" * 70)
    
    workflow_tasks = [
        (workflows["customer_service"], {
            "customer_query": "I need help with my subscription",
            "customer_id": "CUST-12345",
            "priority": "high"
        }),
        (workflows["data_analysis"], {
            "data_source": "sales_database",
            "analysis_type": "quarterly_trends",
            "metrics": ["revenue", "customer_acquisition", "churn"]
        })
    ]
    
    print(f"\n⚡ Executing {len(workflow_tasks)} workflows concurrently...")
    
    try:
        results = await executor.execute_multiple(workflow_tasks)
        
        print(f"\n📊 Concurrent Execution Results:")
        for i, context in enumerate(results, 1):
            status_icon = "✅" if context.status == "completed" else "❌"
            print(f"\n   {i}. {context.workflow_id}")
            print(f"      {status_icon} Status: {context.status}")
            print(f"      Duration: {context.total_duration_ms:.2f}ms")
            print(f"      Nodes: {len(context.node_results)}")
            
            if context.status == "failed":
                print(f"      Error: {context.get_variable('error')}")
    
    except Exception as e:
        print(f"\n❌ Concurrent execution failed: {e}")
    
    # Display execution summary
    print("\n" + "=" * 70)
    print("📈 Execution Summary")
    print("=" * 70)
    
    summary = executor.get_execution_summary()
    print(f"\n   Active Executions: {summary['active_executions']}")
    print(f"   Completed Executions: {summary['completed_executions']}")
    
    if summary['recent_completed']:
        print(f"\n   Recent Completions:")
        for exec_summary in summary['recent_completed'][-5:]:
            status_icon = "✅" if exec_summary['status'] == "completed" else "❌"
            print(f"      {status_icon} {exec_summary['workflow_id']}: {exec_summary['duration_ms']:.2f}ms")
    
    # Get observability data from context manager
    print("\n" + "=" * 70)
    print("🔍 System Observability")
    print("=" * 70)
    
    obs_data = await context_manager.get_observability_summary()
    
    print(f"\n   System Status:")
    sys_status = obs_data['system_status']
    print(f"      - Active Worlds: {sys_status['active_worlds']}")
    print(f"      - Current Executions: {sys_status['current_executions']}")
    print(f"      - Total Completed: {sys_status['total_completed']}")
    print(f"      - Success Rate: {sys_status['success_rate']:.1f}%")
    print(f"      - Avg Duration: {sys_status['avg_duration_ms']:.2f}ms")
    
    if obs_data['agent_usage']:
        print(f"\n   Agent Usage Statistics:")
        for agent, count in obs_data['agent_usage'].items():
            print(f"      - {agent}: {count} executions")
    
    print("\n" + "=" * 70)
    print("✨ Workflow Execution Demo Complete!")
    print("=" * 70)
    print("\n📊 View detailed traces in TensorZero UI: http://localhost:4000")
    print("   - Check 'Inferences' tab for individual LLM calls")
    print("   - View 'Traces' for complete workflow executions")
    print("   - Analyze 'Metrics' for performance data")
    
    # Cleanup
    await context_manager.cleanup()
    await llm_client.close()


async def export_workflow_definitions():
    """
    Export workflow definitions to files for sharing.
    """
    print("\n" + "=" * 70)
    print("💾 Exporting Workflow Definitions")
    print("=" * 70)
    
    workflows = {
        "product_launch": create_product_launch_workflow(),
        "customer_service": create_customer_service_workflow(),
        "data_analysis": create_data_analysis_workflow()
    }
    
    export_dir = Path("workflow_definitions")
    export_dir.mkdir(exist_ok=True)
    
    for name, workflow in workflows.items():
        # Export as YAML
        yaml_path = export_dir / f"{name}.yaml"
        with open(yaml_path, 'w') as f:
            f.write(workflow.to_yaml())
        print(f"   ✓ Exported {name} to {yaml_path}")
        
        # Export as JSON
        json_path = export_dir / f"{name}.json"
        with open(json_path, 'w') as f:
            f.write(workflow.to_json())
        print(f"   ✓ Exported {name} to {json_path}")
    
    print(f"\n✅ All workflows exported to {export_dir}/")


async def main():
    """
    Main demo function.
    """
    print("""
╔════════════════════════════════════════════════════════════════════╗
║     TinyContext Workflow System with Full Observability Demo      ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run demonstration
    await demonstrate_workflow_execution()
    
    # Export definitions
    await export_workflow_definitions()
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                         Demo Complete! 🎉                         ║
║                                                                    ║
║  The workflow system provides:                                    ║
║  • Declarative workflow definitions                               ║
║  • Multi-agent orchestration                                      ║
║  • Parallel and conditional execution                             ║
║  • Full observability through TensorZero                          ║
║  • Reusable workflow patterns                                     ║
║  • Export/import for workflow sharing                             ║
╚════════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    asyncio.run(main())