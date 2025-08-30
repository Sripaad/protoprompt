#!/usr/bin/env python3
"""
CLI for TinyContext - Enhanced with Simple API commands.
"""

import asyncio
import click
import json
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

try:
    from .manager.context_manager import TinyContextManager
    from .inference.tensorzero_client import TensorZeroClient
    from .sessions.session_manager import SessionStore
    HAS_FULL_FRAMEWORK = True
except ImportError:
    HAS_FULL_FRAMEWORK = False

# Always available - Simple API
from .simple import quick_start, setup_environment, run_quick_task

console = Console()


@click.group()
@click.version_option(version="0.0.1")
def cli():
    """TinyContext - FSM-based AI agent orchestration."""
    pass


@cli.command()
@click.argument('task')
@click.option('--input', '-i', help='Input data as JSON string')
@click.option('--agent', '-a', help='Specific agent to use')
@click.option('--session', '-s', help='Session ID for tracking')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run(task, input, agent, session, verbose):
    """Run a task through TinyContext."""
    console.print(f"[bold cyan]🚀 TinyContext v0.0.1[/bold cyan]\n")
    
    # Parse input data
    input_data = {}
    if input:
        try:
            input_data = json.loads(input)
        except json.JSONDecodeError:
            console.print("[red]Error: Invalid JSON input[/red]")
            return
    
    # Initialize components
    llm_client = TensorZeroClient()
    manager = TinyContextManager(llm_client=llm_client)
    
    # Show available agents if verbose
    if verbose:
        agents = manager.get_agent_registry()
        table = Table(title="Available Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Role", style="magenta")
        table.add_column("Persona", style="green")
        
        for agent in agents:
            table.add_row(agent['name'], agent['role'], agent['persona'][:50] + "...")
        
        console.print(table)
        console.print()
    
    # Run task
    console.print(f"[bold]Task:[/bold] {task}")
    if input_data:
        console.print(f"[bold]Input:[/bold] {json.dumps(input_data, indent=2)}")
    console.print()
    
    with console.status("[bold green]Processing...") as status:
        result = manager.run(task, input_data)
    
    # Display result
    if result['success']:
        console.print(Panel(
            result['output'],
            title=f"✅ Success (Agent: {result['agent']})",
            border_style="green"
        ))
        
        if verbose:
            # Show execution trace
            trace = manager.log_trace(result['trace_id'])
            console.print("\n[bold]Execution Trace:[/bold]")
            
            for i, step in enumerate(trace['steps'], 1):
                console.print(f"\n[cyan]Step {i}:[/cyan]")
                console.print(f"  [yellow]Reasoning:[/yellow] {step['reasoning']}")
                console.print(f"  [green]Action:[/green] {step['action']}")
                console.print(f"  [dim]Confidence:[/dim] {step['confidence']:.2f}")
            
            # Show state transitions
            if trace['state_transitions']:
                console.print("\n[bold]State Transitions:[/bold]")
                for transition in trace['state_transitions']:
                    console.print(f"  {transition['from']} → {transition['to']} ({transition['trigger']})")
    else:
        console.print(Panel(
            result['error'],
            title="❌ Error",
            border_style="red"
        ))
    
    # Save to session if specified
    if session:
        store = SessionStore("./sessions")
        if not store.get_session(session):
            store.create_session(session)
        
        trace_data = manager.log_trace(result['trace_id'])
        store.update_session(session, [trace_data])
        console.print(f"\n[dim]Session saved: {session}[/dim]")


@cli.command()
def agents():
    """List available agents."""
    manager = TinyContextManager()
    agents = manager.get_agent_registry()
    
    table = Table(title="TinyContext Agents")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Role", style="magenta")
    table.add_column("Persona", style="green")
    
    for agent in agents:
        table.add_row(
            agent['name'],
            agent['role'],
            agent['persona']
        )
    
    console.print(table)


@cli.command()
def sessions():
    """List sessions."""
    store = SessionStore("./sessions")
    sessions = store.list_sessions()
    
    if not sessions:
        console.print("[yellow]No sessions found[/yellow]")
        return
    
    table = Table(title="Sessions")
    table.add_column("ID", style="cyan")
    table.add_column("Created", style="magenta")
    table.add_column("Traces", style="green")
    
    for session in sessions:
        table.add_row(
            session['id'],
            session['created_at'],
            str(session['trace_count'])
        )
    
    console.print(table)


@cli.command()
@click.argument('session_id')
def replay(session_id):
    """Replay a session."""
    store = SessionStore("./sessions")
    session = store.get_session(session_id)
    
    if not session:
        console.print(f"[red]Session not found: {session_id}[/red]")
        return
    
    console.print(f"[bold cyan]Replaying Session: {session_id}[/bold cyan]\n")
    
    for i, trace in enumerate(session.traces, 1):
        console.print(f"[bold]Trace {i}:[/bold]")
        console.print(f"  Task: {trace.get('task', 'N/A')}")
        console.print(f"  Agent: {trace.get('agent', 'N/A')}")
        
        if 'output' in trace:
            console.print(f"  Output: {trace['output']}")
        if 'error' in trace:
            console.print(f"  [red]Error: {trace['error']}[/red]")
        
        console.print()


@cli.command()
def setup():
    """Interactive setup for TinyContext Simple."""
    console.print("[bold cyan]🚀 TinyContext Simple - Environment Setup[/bold cyan]\n")
    
    # Run environment setup
    status = setup_environment()
    
    if status["openai_key"] and status["dependencies"]:
        console.print("\n[green]🎉 You're ready to use TinyContext Simple![/green]")
        console.print("\nQuick start examples:")
        console.print("  [cyan]tinycontext demo[/cyan]           - Run interactive demo")
        console.print("  [cyan]tinycontext quick 'hello world'[/cyan] - Quick task execution")
        console.print("  [cyan]python -m tinycontext.simple[/cyan]     - Import in Python")
    else:
        console.print("\n[yellow]⚠️  Setup incomplete. Please address the recommendations above.[/yellow]")


@cli.command()
@click.argument('task')
@click.option('--data', '-d', help='Input data as JSON string')
@click.option('--strategy', '-s', 
              type=click.Choice(['auto', 'select', 'compress', 'isolate']),
              default='auto',
              help='Context engineering strategy')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def quick(task, data, strategy, verbose):
    """Quick task execution with TinyContext Simple."""
    async def run_task():
        console.print(f"[bold cyan]🚀 TinyContext Simple - Quick Execution[/bold cyan]\n")
        
        # Parse input data
        input_data = {}
        if data:
            try:
                input_data = json.loads(data)
            except json.JSONDecodeError:
                console.print("[red]Error: Invalid JSON input data[/red]")
                return
        
        console.print(f"[bold]Task:[/bold] {task}")
        if input_data:
            console.print(f"[bold]Data:[/bold] {json.dumps(input_data, indent=2)}")
        console.print(f"[bold]Strategy:[/bold] {strategy}")
        console.print()
        
        try:
            with console.status("[bold green]Processing..."):
                agent = quick_start(verbose=verbose)
                await agent.initialize()
                
                result = await agent.run(
                    task=task,
                    data=input_data,
                    context_strategy=strategy
                )
            
            if result['success']:
                console.print(Panel(
                    result['output'],
                    title=f"✅ Success ({result.get('framework', 'simple')} mode)",
                    border_style="green"
                ))
                
                if verbose:
                    console.print(f"\n[dim]Context Strategy: {result.get('context_strategy', 'auto')}[/dim]")
                    if 'tokens_used' in result:
                        console.print(f"[dim]Tokens Used: {result['tokens_used']}[/dim]")
                    if 'agents_used' in result:
                        console.print(f"[dim]Agents Used: {', '.join(result['agents_used'])}[/dim]")
            else:
                console.print(Panel(
                    result.get('error', 'Unknown error'),
                    title="❌ Error",
                    border_style="red"
                ))
                
        except Exception as e:
            console.print(Panel(
                str(e),
                title="❌ Execution Error",
                border_style="red"
            ))
    
    # Run async task
    asyncio.run(run_task())


@cli.command()
def demo():
    """Run interactive TinyContext Simple demo."""
    async def run_demo():
        console.print("[bold cyan]🚀 TinyContext Simple - Interactive Demo[/bold cyan]\n")
        console.print("This demo shows TinyContext Simple capabilities with context engineering.")
        console.print("Type your questions or tasks. Type 'quit' to exit.\n")
        
        try:
            agent = quick_start(name="demo_agent", verbose=True)
            await agent.initialize()
            
            # Add some demo context
            await agent.add_context(
                "demo_info",
                "This is a demo of TinyContext Simple API featuring context engineering patterns: Write, Select, Compress, and Isolate context.",
                ["demo", "info"]
            )
            
            console.print("[green]✅ Demo agent ready![/green]")
            console.print("Try asking: 'What can you do?', 'Analyze some data', or 'Help me code'\n")
            
            while True:
                try:
                    user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        console.print("\n[bold]Thanks for trying TinyContext Simple! 👋[/bold]")
                        break
                    
                    if not user_input:
                        continue
                    
                    with console.status("[bold green]Thinking..."):
                        result = await agent.run(
                            task=user_input,
                            context_strategy="auto"
                        )
                    
                    if result['success']:
                        console.print(f"[bold green]Agent:[/bold green] {result['output']}\n")
                    else:
                        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]\n")
                        
                except KeyboardInterrupt:
                    console.print("\n\n[bold]Demo interrupted. Thanks for trying TinyContext Simple! 👋[/bold]")
                    break
                    
        except Exception as e:
            console.print(f"[red]Demo initialization error: {e}[/red]")
            console.print("Make sure OPENAI_API_KEY is set in your environment.")
    
    asyncio.run(run_demo())


@cli.command()
def examples():
    """List and run example scripts."""
    console.print("[bold cyan]🚀 TinyContext Simple - Examples[/bold cyan]\n")
    
    examples_dir = Path(__file__).parent.parent / "examples"
    if not examples_dir.exists():
        console.print("[red]Examples directory not found[/red]")
        return
    
    # Find simple examples
    simple_examples = [
        f for f in examples_dir.glob("simple_*.py") 
        if f.is_file()
    ]
    
    if not simple_examples:
        console.print("[yellow]No simple examples found[/yellow]")
        return
    
    console.print("Available examples:")
    for i, example in enumerate(simple_examples, 1):
        name = example.stem.replace('simple_', '').replace('_', ' ').title()
        console.print(f"  {i}. [cyan]{name}[/cyan] - {example.name}")
    
    console.print("\nTo run an example:")
    console.print(f"  [green]python {simple_examples[0]}[/green]")
    
    for example in simple_examples:
        console.print(f"  [green]python {example}[/green]")


@cli.command()
def init():
    """Initialize TinyContext configuration."""
    if HAS_FULL_FRAMEWORK:
        # Create default directories for full framework
        Path("agents").mkdir(exist_ok=True)
        Path("prompts").mkdir(exist_ok=True)
        Path("sessions").mkdir(exist_ok=True)
        
        # Create sample agent config
        sample_agent = {
            "name": "assistant",
            "role": "general",
            "persona": "A helpful AI assistant",
            "prompts": {
                "system": "You are a helpful AI assistant.",
                "reasoning_template": "Let me think about: {input}",
                "action_template": "Based on my analysis: {action}"
            }
        }
        
        with open("agents/assistant.json", "w") as f:
            json.dump(sample_agent, f, indent=2)
    
    # Always create .env example for Simple API
    if not Path(".env").exists():
        env_content = """# TinyContext Configuration
# Preferred: Groq API Key for high-speed inference (~500 tokens/sec)  
GROQ_API_KEY=your-groq-api-key-here

# Fallback: OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here

# Optional settings
TINYCONTEXT_VERBOSE=false
ENABLE_OBSERVABILITY=false
TENSORZERO_MODEL=groq
"""
        with open(".env", "w") as f:
            f.write(env_content)
        
        console.print("[green]✅ Created .env file[/green]")
        console.print("   Edit .env and set your OPENAI_API_KEY")
    
    console.print("[green]✅ TinyContext initialized![/green]")
    
    if HAS_FULL_FRAMEWORK:
        console.print("\nFull framework directories created:")
        console.print("  • agents/ directory")
        console.print("  • prompts/ directory")
        console.print("  • sessions/ directory")
        console.print("  • agents/assistant.json (sample agent)")
    
    console.print("\nNext steps:")
    console.print("  1. Set OPENAI_API_KEY in .env file")
    console.print("  2. Run: [cyan]tinycontext setup[/cyan] to verify configuration")
    console.print("  3. Run: [cyan]tinycontext demo[/cyan] to try interactive demo")


if __name__ == "__main__":
    cli()