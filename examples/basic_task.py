#!/usr/bin/env python3
"""
Basic example of using TinyContext to process a task.
"""

from tinycontext.manager.context_manager import TinyContextManager
from tinycontext.inference.tensorzero_client import TensorZeroClient


def main():
    """Run a basic task through TinyContext."""
    
    # Initialize the system
    llm_client = TensorZeroClient()
    manager = TinyContextManager(llm_client=llm_client)
    
    # Define a task
    task = "Create a strategy for improving customer retention in a SaaS product"
    
    print(f"Task: {task}")
    print("-" * 50)
    
    # Run the task
    result = manager.run(task)
    
    # Display results
    if result['success']:
        print(f"\n✅ Success!")
        print(f"Agent Used: {result['agent']}")
        print(f"\nOutput:\n{result['output']}")
        
        # Get execution trace
        trace = manager.log_trace(result['trace_id'])
        print(f"\nExecution Steps: {len(trace['steps'])}")
        
        for i, step in enumerate(trace['steps'], 1):
            print(f"\nStep {i}:")
            print(f"  Reasoning: {step['reasoning'][:100]}...")
            print(f"  Action: {step['action'][:100]}...")
            
        # Show FSM transitions
        print(f"\nState Transitions:")
        for transition in trace['state_transitions']:
            print(f"  {transition['from']} → {transition['to']}")
    else:
        print(f"\n❌ Error: {result['error']}")


if __name__ == "__main__":
    main()