#!/usr/bin/env python3
"""
CLI for TinyContext.
"""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from .manager.context_manager import TinyContextManager
from .inference.tensorzero_client import TensorZeroClient
from .sessions.session_manager import SessionStore

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
def init():
    """Initialize TinyContext configuration."""
    # Create default directories
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
    
    console.print("[green]✅ TinyContext initialized![/green]")
    console.print("\nCreated:")
    console.print("  • agents/ directory")
    console.print("  • prompts/ directory")
    console.print("  • sessions/ directory")
    console.print("  • agents/assistant.json (sample agent)")


if __name__ == "__main__":
    cli()