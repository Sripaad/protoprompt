#!/usr/bin/env python3
"""
Automatic Workflow Generator - Dynamic Multi-Agent Orchestration

This example demonstrates how TinyContext can automatically generate and execute
complex workflows based on natural language task descriptions. Instead of 
routing to a single agent, it creates multi-step processes with different 
agents handling different phases.

Features:
- Automatic workflow planning from task description
- Dynamic agent assignment based on task requirements  
- Context passing between workflow steps
- Real-time workflow execution with progress tracking
- Workflow templates for common use cases

Usage:
    python examples/auto_workflow_generator.py
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from tinycontext.simple import ContextAgent


@dataclass
class WorkflowStep:
    """Represents a single step in an automatically generated workflow"""
    step_id: str
    agent_role: str
    task_description: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any] = None
    status: str = "pending"  # pending, running, completed, failed
    dependencies: List[str] = None
    estimated_duration: int = 30  # seconds


@dataclass
class GeneratedWorkflow:
    """Represents an automatically generated workflow"""
    workflow_id: str
    original_task: str
    steps: List[WorkflowStep]
    context_data: Dict[str, Any]
    status: str = "created"
    created_at: datetime = None
    completed_at: datetime = None


class AutoWorkflowGenerator:
    """Automatically generates and executes multi-agent workflows"""
    
    def __init__(self):
        self.planner_agent = None
        self.execution_agents = {}
        self.workflow_templates = {}
        self.active_workflows = {}
        
    async def initialize(self):
        """Initialize the workflow generator"""
        print("🔧 Initializing Auto Workflow Generator...")
        
        # Create planning agent
        self.planner_agent = ContextAgent(
            name="workflow_planner",
            storage_path="./workflow_memory"
        )
        await self.planner_agent.initialize()
        
        # Load workflow templates
        await self._load_workflow_templates()
        
        print("✅ Auto Workflow Generator Ready!")
    
    async def _load_workflow_templates(self):
        """Load common workflow patterns"""
        self.workflow_templates = {
            "customer_support": {
                "pattern": ["intake", "analysis", "resolution", "follow_up"],
                "agents": ["support_intake", "issue_analyzer", "solution_provider", "follow_up_specialist"],
                "context_flow": ["ticket_info", "analysis_results", "resolution_plan", "satisfaction_check"]
            },
            "content_creation": {
                "pattern": ["research", "outline", "writing", "editing", "publishing"],
                "agents": ["researcher", "content_strategist", "writer", "editor", "publisher"],
                "context_flow": ["research_data", "content_outline", "draft_content", "edited_content", "published_content"]
            },
            "data_analysis": {
                "pattern": ["collection", "cleaning", "analysis", "visualization", "reporting"],
                "agents": ["data_collector", "data_cleaner", "analyst", "visualizer", "reporter"],
                "context_flow": ["raw_data", "clean_data", "analysis_results", "charts_graphs", "final_report"]
            },
            "product_development": {
                "pattern": ["requirements", "design", "development", "testing", "deployment"],
                "agents": ["requirements_analyst", "designer", "developer", "tester", "deployment_specialist"],
                "context_flow": ["requirements_doc", "design_specs", "code_implementation", "test_results", "deployment_plan"]
            },
            "market_research": {
                "pattern": ["planning", "data_gathering", "competitive_analysis", "synthesis", "recommendations"],
                "agents": ["research_planner", "data_gatherer", "competitive_analyst", "synthesizer", "strategist"],
                "context_flow": ["research_plan", "market_data", "competitor_analysis", "insights", "action_plan"]
            }
        }
        
        print(f"📋 Loaded {len(self.workflow_templates)} workflow templates")
    
    async def analyze_and_generate_workflow(self, task_description: str) -> GeneratedWorkflow:
        """Analyze task and automatically generate appropriate workflow"""
        print(f"🧠 Analyzing task: {task_description}")
        
        # Use planner to analyze task and suggest workflow
        planning_prompt = f"""
        Task: {task_description}
        
        Available workflow templates:
        {json.dumps(list(self.workflow_templates.keys()), indent=2)}
        
        Template details:
        {json.dumps(self.workflow_templates, indent=2)}
        
        Please analyze this task and either:
        1. Select the most appropriate template and customize it
        2. Create a completely new workflow if no template fits
        
        Respond with a JSON structure containing:
        {{
            "template_used": "template_name or custom",
            "workflow_steps": [
                {{
                    "step_id": "step_1",
                    "agent_role": "role_name",
                    "task_description": "what this step does",
                    "inputs": {{"input_key": "description"}},
                    "dependencies": []
                }}
            ],
            "reasoning": "why this workflow structure"
        }}
        """
        
        result = await self.planner_agent.run(
            task=planning_prompt,
            context_strategy="select"
        )
        
        try:
            # Parse the workflow plan
            workflow_plan = self._parse_workflow_plan(result["output"], task_description)
            print(f"📋 Generated workflow with {len(workflow_plan.steps)} steps")
            return workflow_plan
        except Exception as e:
            print(f"⚠️ Failed to parse workflow plan: {e}")
            # Fallback to simple workflow
            return self._create_fallback_workflow(task_description)
    
    def _parse_workflow_plan(self, plan_text: str, original_task: str) -> GeneratedWorkflow:
        """Parse workflow plan from LLM output"""
        workflow_id = f"wf_{int(datetime.now().timestamp())}"
        
        # Try to extract JSON from the response
        try:
            import re
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                # Create a simple workflow if we can't parse JSON
                return self._create_fallback_workflow(original_task)
            
            # Convert to WorkflowStep objects
            steps = []
            for i, step_data in enumerate(plan_data.get("workflow_steps", [])):
                step = WorkflowStep(
                    step_id=step_data.get("step_id", f"step_{i+1}"),
                    agent_role=step_data.get("agent_role", "assistant"),
                    task_description=step_data.get("task_description", ""),
                    inputs=step_data.get("inputs", {}),
                    dependencies=step_data.get("dependencies", [])
                )
                steps.append(step)
            
            return GeneratedWorkflow(
                workflow_id=workflow_id,
                original_task=original_task,
                steps=steps,
                context_data={"template_used": plan_data.get("template_used", "custom")},
                created_at=datetime.now()
            )
            
        except Exception as e:
            print(f"JSON parsing failed: {e}")
            return self._create_fallback_workflow(original_task)
    
    def _create_fallback_workflow(self, task_description: str) -> GeneratedWorkflow:
        """Create a simple fallback workflow when parsing fails"""
        workflow_id = f"wf_{int(datetime.now().timestamp())}"
        
        steps = [
            WorkflowStep(
                step_id="analyze",
                agent_role="analyzer", 
                task_description=f"Analyze and break down: {task_description}",
                inputs={"original_task": task_description}
            ),
            WorkflowStep(
                step_id="execute",
                agent_role="executor",
                task_description="Execute the planned approach", 
                inputs={"analysis": "from_previous_step"},
                dependencies=["analyze"]
            ),
            WorkflowStep(
                step_id="review",
                agent_role="reviewer",
                task_description="Review and finalize results",
                inputs={"execution_results": "from_previous_step"},
                dependencies=["execute"]
            )
        ]
        
        return GeneratedWorkflow(
            workflow_id=workflow_id,
            original_task=task_description,
            steps=steps,
            context_data={"template_used": "fallback"},
            created_at=datetime.now()
        )
    
    async def execute_workflow(self, workflow: GeneratedWorkflow) -> Dict[str, Any]:
        """Execute the generated workflow step by step"""
        print(f"\n🚀 Executing Workflow: {workflow.workflow_id}")
        print(f"📝 Original Task: {workflow.original_task}")
        print(f"🔄 Steps: {len(workflow.steps)}")
        
        workflow.status = "running"
        execution_results = {}
        context_data = workflow.context_data.copy()
        
        for step in workflow.steps:
            # Check dependencies
            if step.dependencies:
                for dep in step.dependencies:
                    if dep not in execution_results:
                        print(f"⚠️ Dependency {dep} not satisfied for step {step.step_id}")
                        step.status = "failed"
                        continue
            
            # Execute step
            print(f"\n⏳ Executing Step: {step.step_id} ({step.agent_role})")
            print(f"   Task: {step.task_description}")
            
            step.status = "running"
            
            try:
                # Create or get agent for this step
                agent = await self._get_or_create_agent(step.agent_role)
                
                # Prepare step context
                step_context = {
                    "step_id": step.step_id,
                    "workflow_context": context_data,
                    "previous_results": execution_results
                }
                step_context.update(step.inputs)
                
                # Execute the step
                result = await agent.run(
                    task=step.task_description,
                    data=step_context,
                    context_strategy="auto"
                )
                
                if result["success"]:
                    step.outputs = {
                        "result": result["output"],
                        "framework": result.get("framework", "simple"),
                        "execution_time": datetime.now().isoformat()
                    }
                    step.status = "completed"
                    execution_results[step.step_id] = step.outputs
                    context_data[f"{step.step_id}_output"] = result["output"]
                    
                    print(f"   ✅ Completed: {result['output'][:100]}...")
                else:
                    step.status = "failed"
                    print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                step.status = "failed"
                print(f"   ❌ Error: {e}")
        
        # Finalize workflow
        workflow.status = "completed"
        workflow.completed_at = datetime.now()
        
        # Generate workflow summary
        summary_agent = await self._get_or_create_agent("summarizer")
        summary_result = await summary_agent.run(
            task=f"Create a comprehensive summary of this completed workflow",
            data={
                "original_task": workflow.original_task,
                "steps_executed": len([s for s in workflow.steps if s.status == "completed"]),
                "execution_results": execution_results,
                "context_data": context_data
            }
        )
        
        return {
            "workflow_id": workflow.workflow_id,
            "original_task": workflow.original_task,
            "status": workflow.status,
            "steps_completed": len([s for s in workflow.steps if s.status == "completed"]),
            "total_steps": len(workflow.steps),
            "execution_results": execution_results,
            "summary": summary_result.get("output", "Summary generation failed"),
            "duration_seconds": (workflow.completed_at - workflow.created_at).total_seconds()
        }
    
    async def _get_or_create_agent(self, role: str) -> ContextAgent:
        """Get or create an agent for the specified role"""
        if role not in self.execution_agents:
            self.execution_agents[role] = ContextAgent(
                name=f"workflow_{role}",
                storage_path=f"./workflow_memory/{role}"
            )
            await self.execution_agents[role].initialize()
        
        return self.execution_agents[role]
    
    async def run_auto_workflow(self, task_description: str) -> Dict[str, Any]:
        """Complete workflow: analyze, generate, and execute"""
        print(f"\n🎯 Auto Workflow Request: {task_description}")
        
        # Step 1: Generate workflow
        workflow = await self.analyze_and_generate_workflow(task_description)
        
        # Step 2: Execute workflow
        results = await self.execute_workflow(workflow)
        
        return results


async def demo_automatic_workflows():
    """Demonstrate automatic workflow generation for various tasks"""
    print("🤖 Automatic Workflow Generator Demo")
    print("=" * 50)
    
    # Initialize generator
    generator = AutoWorkflowGenerator()
    await generator.initialize()
    
    # Demo tasks that should generate different workflows
    demo_tasks = [
        "Handle a customer complaint about billing issues",
        "Create a marketing campaign for a new product launch", 
        "Analyze sales data and provide business insights",
        "Design and develop a mobile app feature",
        "Research competitors and create a market analysis report"
    ]
    
    for i, task in enumerate(demo_tasks, 1):
        print(f"\n{'='*60}")
        print(f"🎯 Demo {i}: {task}")
        print('='*60)
        
        try:
            results = await generator.run_auto_workflow(task)
            
            print(f"\n📊 Workflow Results:")
            print(f"   Status: {results['status']}")
            print(f"   Steps: {results['steps_completed']}/{results['total_steps']}")
            print(f"   Duration: {results['duration_seconds']:.2f}s")
            print(f"\n📋 Summary:")
            print(f"   {results['summary']}")
            
        except Exception as e:
            print(f"❌ Demo {i} failed: {e}")
        
        # Pause between demos
        await asyncio.sleep(2)


async def interactive_workflow_mode():
    """Interactive mode for custom workflow generation"""
    print("\n🤖 Interactive Workflow Generator")
    print("Describe any task and watch as workflows are automatically generated!")
    print("Type 'quit' to exit.\n")
    
    generator = AutoWorkflowGenerator()
    await generator.initialize()
    
    while True:
        try:
            task = input("🎯 Describe your task: ").strip()
            
            if task.lower() in ['quit', 'exit', 'q']:
                break
            
            if not task:
                continue
            
            print("\n🧠 Generating automatic workflow...")
            results = await generator.run_auto_workflow(task)
            
            print(f"\n✅ Workflow Complete!")
            print(f"📊 Results: {results['steps_completed']}/{results['total_steps']} steps")
            print(f"⏱️  Duration: {results['duration_seconds']:.1f}s")
            print(f"\n📋 Summary: {results['summary'][:300]}...")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main():
    """Main entry point"""
    print("TinyContext Automatic Workflow Generator")
    print("Choose mode:")
    print("1. Automated demo (5 different workflow types)")
    print("2. Interactive mode (describe your own tasks)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            await demo_automatic_workflows()
        elif choice == "2":
            await interactive_workflow_mode()
        else:
            print("Invalid choice. Running demo...")
            await demo_automatic_workflows()
            
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have:")
        print("1. Set GROQ_API_KEY in your environment")
        print("2. Installed dependencies: pip install tinycontext")


if __name__ == "__main__":
    asyncio.run(main())