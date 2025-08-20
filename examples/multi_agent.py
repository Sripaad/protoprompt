#!/usr/bin/env python3
"""
Example of multi-agent handoff in TinyContext.
"""

from tinycontext.manager.context_manager import TinyContextManager
from tinycontext.agents.loader import TinyFactory, TinyPerson, Prompts
from tinycontext.inference.tensorzero_client import TensorZeroClient


def setup_custom_agents():
    """Create custom agents for the example."""
    factory = TinyFactory()
    
    # Create a custom strategist
    strategist = TinyPerson(
        name="strategy_expert",
        role="strategist",
        persona="Expert at breaking down complex problems into strategic components",
        prompts=Prompts(
            system="You are a strategic thinker. Always consider multiple perspectives.",
            reasoning_template="Analyzing strategically: {input}",
            action_template="Strategic recommendation: {action}"
        )
    )
    
    # Create a custom analyst
    analyst = TinyPerson(
        name="data_analyst",
        role="analyzer",
        persona="Data-driven analyst who loves metrics and patterns",
        prompts=Prompts(
            system="You are a data analyst. Focus on measurable insights.",
            reasoning_template="Analyzing data and patterns: {input}",
            action_template="Data insights: {action}\nHANDOFF: planner"
        )
    )
    
    # Create a custom planner
    planner = TinyPerson(
        name="execution_planner",
        role="planner",
        persona="Detail-oriented planner who creates actionable plans",
        prompts=Prompts(
            system="You are a project planner. Create executable plans.",
            reasoning_template="Planning execution: {input}",
            action_template="Execution plan: {action}"
        )
    )
    
    # Register agents
    factory.register_agent(strategist)
    factory.register_agent(analyst)
    factory.register_agent(planner)
    
    return factory


def main():
    """Demonstrate multi-agent handoff."""
    
    print("🤖 Multi-Agent Handoff Example\n")
    
    # Setup custom agents
    factory = setup_custom_agents()
    
    # Initialize manager with custom factory
    llm_client = TensorZeroClient()
    manager = TinyContextManager(llm_client=llm_client)
    manager.factory = factory  # Use our custom factory
    
    # Task that will trigger handoffs
    task = "Analyze our customer churn data and create an action plan"
    
    print(f"Task: {task}")
    print("=" * 60)
    
    # Run the task (should trigger analyzer → planner handoff)
    result = manager.run(task)
    
    if result['success']:
        print(f"\n✅ Task completed successfully!")
        print(f"Primary Agent: {result['agent']}")
        print(f"\nFinal Output:\n{result['output']}")
        
        # Show the handoff chain
        trace = manager.log_trace(result['trace_id'])
        print(f"\n🔄 Agent Handoff Chain:")
        
        for step in trace['steps']:
            agent_name = step.get('metadata', {}).get('agent', 'unknown')
            handoff = step.get('metadata', {}).get('handoff')
            
            print(f"  • {agent_name}")
            if handoff:
                print(f"    ↓ (hands off to {handoff})")
        
        # Show FSM state flow
        print(f"\n📊 FSM State Flow:")
        for transition in trace['state_transitions']:
            print(f"  {transition['from']} → {transition['to']} ({transition['trigger']})")
            
    else:
        print(f"\n❌ Error: {result['error']}")
    
    print("\n" + "=" * 60)
    print("Example complete!")


if __name__ == "__main__":
    main()