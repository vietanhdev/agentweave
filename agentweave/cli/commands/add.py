"""
Command to add components to an AgentWeave project.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

from agentweave.utils.config import (
    get_available_memories,
    get_available_monitors,
    get_available_tools,
    is_agentweave_project,
)
from agentweave.utils.templates import copy_template_dir, render_template_file

app = typer.Typer(
    name="add",
    help="Add components to an AgentWeave project",
    add_completion=False,
)

console = Console()


@app.callback()
def callback():
    """
    Add components to an AgentWeave project.
    """
    # Check if current directory is an AgentWeave project
    if not is_agentweave_project():
        console.print(
            "[red]Not an AgentWeave project. Run this command from the project root.[/red]"
        )
        raise typer.Exit(1)


@app.command()
def tool(
    tool_name: str = typer.Argument(..., help="Name of the tool to add"),
    custom: bool = typer.Option(
        False,
        "--custom",
        "-c",
        help="Create a custom tool instead of using a predefined one",
    ),
):
    """
    Add a tool to the project.

    Examples:
        agentweave add tool web-search
        agentweave add tool my-custom-tool --custom
    """
    project_dir = Path.cwd()

    if custom:
        # Create a custom tool
        console.print(
            f"[bold cyan]Creating custom tool: [/bold cyan][bold white]{tool_name}[/bold white]"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}[/bold cyan]"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating custom tool...", total=None)

            settings = {
                "tool_name": tool_name,
                "tool_description": Prompt.ask(
                    "Tool description",
                    default=f"A custom tool for {tool_name}",
                ),
            }

            # Create the tool from the custom template
            render_template_file(
                "custom_tool.py.jinja2",
                project_dir / "tools" / f"{tool_name.replace('-', '_')}.py",
                settings,
            )

            progress.update(task, description="Custom tool created successfully!")

        console.print(
            f"\n[bold green]✓ Custom tool '{tool_name}' created successfully![/bold green]"
        )
    else:
        # Add a predefined tool
        available_tools = get_available_tools()
        if tool_name not in available_tools:
            console.print(f"[red]Tool '{tool_name}' not found. Available tools:[/red]")
            for t in available_tools:
                console.print(f"  - {t}")
            raise typer.Exit(1)

        console.print(
            f"[bold cyan]Adding tool: [/bold cyan][bold white]{tool_name}[/bold white]"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}[/bold cyan]"),
            console=console,
        ) as progress:
            task = progress.add_task("Adding tool...", total=None)

            # Copy the tool template
            copy_template_dir(f"tools/{tool_name}", project_dir / "tools", {})

            progress.update(task, description="Tool added successfully!")

        console.print(
            f"\n[bold green]✓ Tool '{tool_name}' added successfully![/bold green]"
        )


@app.command()
def memory(
    memory_type: str = typer.Argument(..., help="Type of memory to add"),
):
    """
    Add a memory component to the project.

    Examples:
        agentweave add memory simple
        agentweave add memory vector-store
    """
    project_dir = Path.cwd()

    available_memories = get_available_memories()
    if memory_type not in available_memories:
        console.print(
            f"[red]Memory type '{memory_type}' not found. Available memory types:[/red]"
        )
        for m in available_memories:
            console.print(f"  - {m}")
        raise typer.Exit(1)

    console.print(
        f"[bold cyan]Adding memory: [/bold cyan][bold white]{memory_type}[/bold white]"
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        console=console,
    ) as progress:
        task = progress.add_task("Adding memory component...", total=None)

        # Copy the memory template
        copy_template_dir(f"memory/{memory_type}", project_dir / "memory", {})

        progress.update(task, description="Memory component added successfully!")

    console.print(
        f"\n[bold green]✓ Memory component '{memory_type}' added successfully![/bold green]"
    )


@app.command()
def monitor(
    monitor_name: str = typer.Argument(
        ..., help="Name of the monitoring component to add"
    ),
):
    """
    Add a monitoring component to the project.

    Examples:
        agentweave add monitor tracing
        agentweave add monitor dashboard
    """
    project_dir = Path.cwd()

    available_monitors = get_available_monitors()
    if monitor_name not in available_monitors:
        console.print(
            f"[red]Monitor '{monitor_name}' not found. Available monitors:[/red]"
        )
        for m in available_monitors:
            console.print(f"  - {m}")
        raise typer.Exit(1)

    console.print(
        f"[bold cyan]Adding monitor: [/bold cyan][bold white]{monitor_name}[/bold white]"
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        console=console,
    ) as progress:
        task = progress.add_task("Adding monitoring component...", total=None)

        # Copy the monitor template
        copy_template_dir(f"monitoring/{monitor_name}", project_dir / "monitoring", {})

        progress.update(task, description="Monitoring component added successfully!")

    console.print(
        f"\n[bold green]✓ Monitoring component '{monitor_name}' added successfully![/bold green]"
    )


if __name__ == "__main__":
    app()
