"""
Command to list available components in AgentWeave.
"""

import typer
from rich.console import Console
from rich.table import Table

from agentweave.utils.config import (
    get_available_memories,
    get_available_monitors,
    get_available_templates,
    get_available_tools,
)

app = typer.Typer(
    name="list",
    help="List available components in AgentWeave",
    add_completion=False,
)

console = Console()


@app.callback()
def callback():
    """
    List available components in AgentWeave.
    """
    pass


@app.command()
def templates():
    """
    List available project templates.

    Examples:
        agentweave list templates
    """
    templates = get_available_templates()

    table = Table(title="Available Templates")
    table.add_column("Template", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    template_descriptions = {
        "basic": "A simple agent with minimal components",
        "conversational": "A conversational agent optimized for chat",
        "reasoning": "An agent with advanced reasoning capabilities",
        "tool-using": "An agent focused on using tools effectively",
        "advanced": "A fully-featured agent with all components",
    }

    for template in sorted(templates):
        description = template_descriptions.get(template, "")
        table.add_row(template, description)

    console.print(table)


@app.command(name="tools")
def list_tools():
    """
    List available tools.

    Examples:
        agentweave list tools
    """
    tools = get_available_tools()

    table = Table(title="Available Tools")
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    tool_descriptions = {
        "web-search": "Search the web for information",
        "file-io": "Read and write files",
        "calculator": "Perform calculations",
        "weather": "Get weather information",
        "wikipedia": "Query Wikipedia",
        "calendar": "Manage calendar events",
        "email": "Send and receive emails",
        "code-interpreter": "Run Python code",
        "database": "Query databases",
        "api-connector": "Connect to external APIs",
    }

    for tool in sorted(tools):
        description = tool_descriptions.get(tool, "")
        table.add_row(tool, description)

    console.print(table)


@app.command(name="memories")
def list_memories():
    """
    List available memory components.

    Examples:
        agentweave list memories
    """
    memories = get_available_memories()

    table = Table(title="Available Memory Components")
    table.add_column("Memory", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    memory_descriptions = {
        "simple": "Basic in-memory storage",
        "vector-store": "Vector-based retrieval memory",
        "conversation": "Conversation history tracker",
        "document": "Document storage and retrieval",
        "redis": "Redis-backed persistent memory",
    }

    for memory in sorted(memories):
        description = memory_descriptions.get(memory, "")
        table.add_row(memory, description)

    console.print(table)


@app.command(name="monitors")
def list_monitors():
    """
    List available monitoring components.

    Examples:
        agentweave list monitors
    """
    monitors = get_available_monitors()

    table = Table(title="Available Monitoring Components")
    table.add_column("Monitor", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    monitor_descriptions = {
        "tracing": "Tracing and logging for agent actions",
        "dashboard": "Web dashboard for monitoring agents",
        "metrics": "Metrics collection and visualization",
        "debugger": "Interactive debugger for agents",
        "langfuse": "Langfuse integration for observability",
    }

    for monitor in sorted(monitors):
        description = monitor_descriptions.get(monitor, "")
        table.add_row(monitor, description)

    console.print(table)


@app.command()
def components():
    """
    List all available components.

    Examples:
        agentweave list components
    """
    console.print("[bold cyan]Available Components in AgentWeave[/bold cyan]\n")

    console.print("[bold]Templates:[/bold]")
    templates()

    console.print("\n[bold]Tools:[/bold]")
    list_tools()

    console.print("\n[bold]Memory Components:[/bold]")
    list_memories()

    console.print("\n[bold]Monitoring Components:[/bold]")
    list_monitors()


if __name__ == "__main__":
    app()
