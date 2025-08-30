#!/usr/bin/env python3
"""
Smart Workflow Orchestrator - Automatic Multi-Agent Coordination

This example demonstrates how TinyContext can automatically orchestrate 
complex workflows by:
1. Analyzing task complexity and requirements
2. Dynamically creating agent teams
3. Managing context flow between agents
4. Adapting workflows based on intermediate results

This is the "smart orchestration" that makes workflows emerge naturally
from the task description, rather than pre-defining rigid workflows.

Usage:
    python examples/smart_workflow_orchestrator.py
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from tinycontext.simple import ContextAgent


class SmartOrchestrator:
    """Intelligent workflow orchestrator that creates agent teams dynamically"""
    
    def __init__(self):
        self.coordinator_agent = None
        self.active_agents = {}
        self.workflow_memory = {}
        
    async def initialize(self):
        """Initialize the orchestrator"""
        print("🧠 Initializing Smart Workflow Orchestrator...")
        
        # Create coordinator agent that manages other agents
        self.coordinator_agent = ContextAgent(
            name="smart_coordinator",
            storage_path="./orchestrator_memory"
        )
        await self.coordinator_agent.initialize()
        
        # Pre-load coordination strategies
        await self._load_orchestration_patterns()
        
        print("✅ Smart Orchestrator Ready!")
    
    async def _load_orchestration_patterns(self):
        """Load patterns for smart orchestration"""
        patterns = {
            "sequential_processing": "Steps must be completed in order, each depends on the previous",
            "parallel_processing": "Multiple steps can run simultaneously, then results are merged",
            "iterative_refinement": "Results are improved through multiple rounds of feedback",
            "divide_and_conquer": "Complex task is broken into smaller independent parts",
            "expert_consultation": "Multiple specialists provide input on the same problem",
            "pipeline_processing": "Data flows through multiple transformation stages"
        }
        
        for pattern_name, description in patterns.items():
            await self.coordinator_agent.add_context(
                f"pattern_{pattern_name}",
                description,
                ["orchestration", "pattern"],
                persistent=True
            )
        
        print(f"📋 Loaded {len(patterns)} orchestration patterns")
    
    async def orchestrate_smart_workflow(self, task_description: str) -> Dict[str, Any]:
        """Automatically analyze task and create appropriate workflow"""
        print(f"\n🎯 Smart Orchestration Request: {task_description}")
        
        # Step 1: Analyze task complexity and requirements
        analysis = await self._analyze_task_requirements(task_description)
        print(f"📊 Task Analysis: {analysis['complexity']} complexity, {analysis['agent_count']} agents needed")
        
        # Step 2: Create agent team based on requirements
        agent_team = await self._assemble_agent_team(analysis)
        print(f"👥 Assembled team: {', '.join(agent_team.keys())}")
        
        # Step 3: Execute with dynamic coordination
        results = await self._execute_coordinated_workflow(task_description, analysis, agent_team)
        
        return results
    
    async def _analyze_task_requirements(self, task: str) -> Dict[str, Any]:
        """Analyze what kind of workflow this task needs"""
        analysis_prompt = f"""
        Analyze this task and determine the workflow requirements:
        Task: {task}
        
        Consider:
        1. What types of expertise are needed?
        2. Can steps run in parallel or must they be sequential?
        3. How many agents would be optimal?
        4. What orchestration pattern fits best?
        5. What context needs to flow between steps?
        
        Respond with JSON:
        {{
            "complexity": "simple|moderate|complex",
            "agent_count": number,
            "required_roles": ["role1", "role2"],
            "orchestration_pattern": "sequential|parallel|iterative|divide_conquer|expert_consultation|pipeline",
            "context_flow": "what information flows between steps",
            "estimated_duration": "time estimate in minutes"
        }}
        """
        
        result = await self.coordinator_agent.run(
            task=analysis_prompt,
            context_strategy="select"
        )
        
        try:
            # Parse analysis results
            import re
            json_match = re.search(r'\{.*\}', result["output"], re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback analysis
                analysis = {
                    "complexity": "moderate",
                    "agent_count": 3,
                    "required_roles": ["analyzer", "processor", "synthesizer"],
                    "orchestration_pattern": "sequential",
                    "context_flow": "results pass from one agent to the next",
                    "estimated_duration": "5-10 minutes"
                }
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Analysis parsing failed: {e}")
            # Return default analysis
            return {
                "complexity": "moderate", 
                "agent_count": 2,
                "required_roles": ["analyzer", "executor"],
                "orchestration_pattern": "sequential",
                "context_flow": "analysis results to executor",
                "estimated_duration": "3-5 minutes"
            }
    
    async def _assemble_agent_team(self, analysis: Dict[str, Any]) -> Dict[str, ContextAgent]:
        """Create the right agents for this workflow"""
        agent_team = {}
        
        for role in analysis["required_roles"]:
            if role not in self.active_agents:
                # Create specialized agent for this role
                agent = ContextAgent(
                    name=f"smart_{role}",
                    storage_path=f"./orchestrator_memory/{role}"
                )
                await agent.initialize()
                
                # Give agent role-specific context
                role_context = self._get_role_context(role)
                await agent.add_context(
                    f"{role}_expertise",
                    role_context,
                    [role, "expertise"],
                    persistent=True
                )
                
                self.active_agents[role] = agent
            
            agent_team[role] = self.active_agents[role]
        
        return agent_team
    
    def _get_role_context(self, role: str) -> str:
        """Get specialized context for different agent roles"""
        role_contexts = {
            "analyzer": "You are an expert analyst who breaks down complex problems, identifies patterns, and provides structured insights.",
            "researcher": "You are a skilled researcher who gathers comprehensive information, evaluates sources, and synthesizes findings.",
            "strategist": "You are a strategic thinker who develops plans, considers alternatives, and recommends optimal approaches.",
            "processor": "You are a data processor who transforms information, applies rules, and generates structured outputs.",
            "synthesizer": "You are a synthesizer who combines multiple inputs, resolves conflicts, and creates unified conclusions.",
            "evaluator": "You are an evaluator who assesses quality, identifies issues, and recommends improvements.",
            "coordinator": "You are a coordinator who manages workflows, resolves dependencies, and ensures smooth execution.",
            "specialist": "You are a domain specialist with deep expertise in your area of focus.",
            "quality_checker": "You are a quality assurance specialist who reviews work and ensures standards are met.",
            "communicator": "You are a communication specialist who creates clear, engaging, and appropriate messaging."
        }
        
        return role_contexts.get(role, f"You are a {role} who excels in your specialized area of expertise.")
    
    async def _execute_coordinated_workflow(self, 
                                          task: str,
                                          analysis: Dict[str, Any], 
                                          agent_team: Dict[str, ContextAgent]) -> Dict[str, Any]:
        """Execute workflow using the determined orchestration pattern"""
        
        pattern = analysis["orchestration_pattern"]
        print(f"🔄 Executing {pattern} orchestration pattern")
        
        start_time = datetime.now()
        workflow_context = {
            "original_task": task,
            "workflow_id": f"smart_{int(datetime.now().timestamp())}",
            "pattern": pattern,
            "agents": list(agent_team.keys())
        }
        
        if pattern == "sequential":
            results = await self._execute_sequential(task, agent_team, workflow_context)
        elif pattern == "parallel":
            results = await self._execute_parallel(task, agent_team, workflow_context)
        elif pattern == "iterative":
            results = await self._execute_iterative(task, agent_team, workflow_context)
        elif pattern == "expert_consultation":
            results = await self._execute_expert_consultation(task, agent_team, workflow_context)
        else:
            # Default to sequential
            results = await self._execute_sequential(task, agent_team, workflow_context)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Create final summary
        summary = await self._create_workflow_summary(task, results, duration, workflow_context)
        
        return {
            "workflow_id": workflow_context["workflow_id"],
            "original_task": task,
            "orchestration_pattern": pattern,
            "agents_used": list(agent_team.keys()),
            "duration_seconds": duration,
            "step_results": results,
            "summary": summary,
            "success": True
        }
    
    async def _execute_sequential(self, task: str, agents: Dict[str, ContextAgent], context: Dict) -> List[Dict]:
        """Execute agents in sequence, passing results forward"""
        results = []
        current_input = task
        
        for i, (role, agent) in enumerate(agents.items()):
            print(f"  📍 Step {i+1}: {role}")
            
            step_task = f"As a {role}, handle this step of the workflow: {current_input}"
            if i > 0:
                step_task += f"\n\nPrevious results: {results[-1]['output'][:500]}..."
            
            result = await agent.run(
                task=step_task,
                data={
                    "step_number": i + 1,
                    "role": role,
                    "workflow_context": context,
                    "previous_results": results
                },
                context_strategy="auto"
            )
            
            step_result = {
                "step": i + 1,
                "role": role,
                "output": result["output"],
                "success": result["success"]
            }
            results.append(step_result)
            
            # Use this result as input for next step
            current_input = result["output"]
            
            print(f"    ✅ {result['output'][:100]}...")
        
        return results
    
    async def _execute_parallel(self, task: str, agents: Dict[str, ContextAgent], context: Dict) -> List[Dict]:
        """Execute agents in parallel, then synthesize results"""
        print(f"  ⚡ Running {len(agents)} agents in parallel")
        
        # Create tasks for each agent
        tasks = []
        for role, agent in agents.items():
            agent_task = f"As a {role}, provide your perspective on: {task}"
            task_coroutine = agent.run(
                task=agent_task,
                data={
                    "role": role,
                    "workflow_context": context
                },
                context_strategy="auto"
            )
            tasks.append((role, task_coroutine))
        
        # Execute all agents concurrently
        parallel_results = []
        for role, task_coro in tasks:
            result = await task_coro
            parallel_results.append({
                "role": role,
                "output": result["output"],
                "success": result["success"]
            })
            print(f"    ✅ {role}: {result['output'][:100]}...")
        
        # Synthesize results
        if "synthesizer" in agents:
            synthesizer = agents["synthesizer"]
        else:
            # Create temporary synthesizer
            synthesizer = ContextAgent(name="temp_synthesizer")
            await synthesizer.initialize()
        
        synthesis_task = f"""
        Synthesize these parallel results into a unified response for: {task}
        
        Results to synthesize:
        {json.dumps([r["output"] for r in parallel_results], indent=2)}
        """
        
        synthesis = await synthesizer.run(synthesis_task, context_strategy="compress")
        
        parallel_results.append({
            "role": "synthesizer",
            "output": synthesis["output"],
            "success": synthesis["success"]
        })
        
        return parallel_results
    
    async def _execute_iterative(self, task: str, agents: Dict[str, ContextAgent], context: Dict) -> List[Dict]:
        """Execute with iterative refinement"""
        results = []
        current_result = task
        
        # First pass through all agents
        for i, (role, agent) in enumerate(agents.items()):
            result = await agent.run(
                f"As a {role}, work on: {current_result}",
                data={"iteration": 1, "role": role, "workflow_context": context},
                context_strategy="auto"
            )
            current_result = result["output"]
            results.append({
                "iteration": 1,
                "role": role,
                "output": result["output"],
                "success": result["success"]
            })
        
        # Refinement pass
        print("  🔄 Refinement iteration...")
        refined_results = []
        for i, (role, agent) in enumerate(agents.items()):
            refine_task = f"""
            As a {role}, refine and improve this work: {current_result}
            
            Consider the full context and previous iterations to make improvements.
            """
            
            result = await agent.run(
                refine_task,
                data={"iteration": 2, "role": role, "previous_results": results},
                context_strategy="compress"
            )
            
            refined_results.append({
                "iteration": 2,
                "role": role,
                "output": result["output"],
                "success": result["success"]
            })
        
        return results + refined_results
    
    async def _execute_expert_consultation(self, task: str, agents: Dict[str, ContextAgent], context: Dict) -> List[Dict]:
        """Get expert opinions, then create unified recommendation"""
        print(f"  👥 Consulting {len(agents)} experts")
        
        # Get expert opinions in parallel
        expert_opinions = []
        tasks = []
        
        for role, agent in agents.items():
            expert_task = f"As an expert {role}, provide your professional opinion on: {task}"
            task_coro = agent.run(
                expert_task,
                data={"expert_role": role, "consultation_context": context},
                context_strategy="select"
            )
            tasks.append((role, task_coro))
        
        for role, task_coro in tasks:
            result = await task_coro
            expert_opinions.append({
                "expert": role,
                "opinion": result["output"],
                "success": result["success"]
            })
            print(f"    🧠 {role}: {result['output'][:80]}...")
        
        # Create unified recommendation
        coordinator_task = f"""
        Based on these expert opinions, create a unified recommendation for: {task}
        
        Expert Opinions:
        {json.dumps([{e["expert"]: e["opinion"]} for e in expert_opinions], indent=2)}
        
        Provide a balanced recommendation that considers all expert input.
        """
        
        final_recommendation = await self.coordinator_agent.run(
            coordinator_task,
            context_strategy="compress"
        )
        
        expert_opinions.append({
            "expert": "coordinator",
            "opinion": final_recommendation["output"],
            "success": final_recommendation["success"]
        })
        
        return expert_opinions
    
    async def _create_workflow_summary(self, task: str, results: List[Dict], duration: float, context: Dict) -> str:
        """Create comprehensive workflow summary"""
        summary_task = f"""
        Create a comprehensive summary of this smart workflow execution:
        
        Original Task: {task}
        Orchestration Pattern: {context['pattern']}
        Agents Used: {', '.join(context['agents'])}
        Duration: {duration:.2f} seconds
        Steps Executed: {len(results)}
        
        Results Summary:
        {json.dumps(results, indent=2)[:1000]}...
        
        Provide a clear, concise summary highlighting:
        1. What was accomplished
        2. How the orchestration worked
        3. Key insights or outputs
        4. Overall success assessment
        """
        
        summary_result = await self.coordinator_agent.run(
            summary_task,
            context_strategy="compress"
        )
        
        return summary_result.get("output", "Summary generation failed")


async def demo_smart_orchestration():
    """Demonstrate smart workflow orchestration with various task types"""
    print("🧠 Smart Workflow Orchestrator Demo")
    print("=" * 50)
    
    orchestrator = SmartOrchestrator()
    await orchestrator.initialize()
    
    # Demo tasks that should trigger different orchestration patterns
    demo_tasks = [
        "Analyze customer feedback and create an action plan",  # Sequential
        "Research three investment options and recommend the best one",  # Expert consultation
        "Create a marketing strategy for a new product launch",  # Iterative
        "Compare pricing strategies across different markets",  # Parallel
        "Design a customer onboarding process"  # Sequential with feedback
    ]
    
    for i, task in enumerate(demo_tasks, 1):
        print(f"\n{'='*70}")
        print(f"🎯 Smart Orchestration Demo {i}")
        print(f"Task: {task}")
        print('='*70)
        
        try:
            results = await orchestrator.orchestrate_smart_workflow(task)
            
            print(f"\n📊 Orchestration Results:")
            print(f"   Pattern Used: {results['orchestration_pattern']}")
            print(f"   Agents: {', '.join(results['agents_used'])}")
            print(f"   Duration: {results['duration_seconds']:.2f}s")
            print(f"   Steps: {len(results['step_results'])}")
            print(f"\n📋 Summary:")
            print(f"   {results['summary'][:400]}...")
            
        except Exception as e:
            print(f"❌ Demo {i} failed: {e}")
        
        # Brief pause between demos
        await asyncio.sleep(1)


async def interactive_orchestrator():
    """Interactive mode for custom smart orchestration"""
    print("\n🧠 Interactive Smart Orchestrator")
    print("Describe any complex task and watch intelligent workflows emerge!")
    print("Type 'quit' to exit.\n")
    
    orchestrator = SmartOrchestrator()
    await orchestrator.initialize()
    
    while True:
        try:
            task = input("🎯 Describe your complex task: ").strip()
            
            if task.lower() in ['quit', 'exit', 'q']:
                break
            
            if not task:
                continue
            
            print(f"\n🧠 Analyzing task and creating smart workflow...")
            results = await orchestrator.orchestrate_smart_workflow(task)
            
            print(f"\n✅ Smart Workflow Complete!")
            print(f"🎯 Pattern: {results['orchestration_pattern']}")
            print(f"👥 Team: {', '.join(results['agents_used'])}")
            print(f"⏱️  Time: {results['duration_seconds']:.1f}s")
            print(f"\n📋 Summary: {results['summary'][:300]}...")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main():
    """Main entry point"""
    print("TinyContext Smart Workflow Orchestrator")
    print("Automatic multi-agent coordination that adapts to any task!")
    print("\nChoose mode:")
    print("1. Automated demo (5 different orchestration patterns)")
    print("2. Interactive mode (describe your own complex tasks)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            await demo_smart_orchestration()
        elif choice == "2":
            await interactive_orchestrator()
        else:
            print("Invalid choice. Running demo...")
            await demo_smart_orchestration()
            
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have:")
        print("1. Set GROQ_API_KEY in your environment (preferred for speed)")
        print("2. Or set OPENAI_API_KEY as fallback")
        print("3. TinyContext properly configured")


if __name__ == "__main__":
    asyncio.run(main())