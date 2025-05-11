"""
AgentWeave CLI - A tool for initializing and managing AI agent projects based on LangGraph.
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agentweave.cli.commands import (
    add,
    convert_to_template,
    deploy,
    dev,
    init,
    install_env,
    list_cmd,
    run,
    template,
)

# Create Typer app
app = typer.Typer(
    name="agentweave",
    help="CLI tool for initializing and managing AI agent projects based on LangGraph",
    add_completion=False,
)

# Register commands
app.command(name="init")(init.app)  # Register init as a direct command
app.add_typer(add.app, name="add")
app.add_typer(list_cmd.app, name="list")
app.command(name="run")(run.app)  # Register run as a direct command
app.add_typer(deploy.app, name="deploy")
app.add_typer(template.app, name="template")
app.add_typer(convert_to_template.app, name="convert-to-template")
app.command(name="install_env")(install_env.app)  # Register install_env as a direct command
app.command(name="dev")(dev.app)  # Register dev as a direct command

console = Console()


@app.callback()
def callback():
    """
    AgentWeave CLI - A tool for initializing and managing AI agent projects based on LangGraph.
    """
    pass


@app.command()
def version():
    """Show the current version of AgentWeave"""
    from agentweave import __version__

    console.print(f"AgentWeave v{__version__}")


@app.command()
def info():
    """Display information about AgentWeave"""
    from agentweave import __version__

    title = Text("AgentWeave", style="bold cyan")
    version_text = Text(f"v{__version__}", style="cyan")

    info_text = Text.from_markup(
        "A CLI tool for initializing and managing AI agent projects based on LangGraph.\n\n"
        "Commands:\n"
        "  [bold]init[/bold]    - Initialize a new agent project\n"
        "  [bold]add[/bold]     - Add components to your project\n"
        "  [bold]list[/bold]    - List available components\n"
        "  [bold]run[/bold]     - Run your agent in development mode\n"
        "  [bold]deploy[/bold]  - Deploy your agent\n"
        "\nFor more information, run: [bold]agentweave --help[/bold]"
    )

    panel = Panel(
        info_text,
        title=f"{title} {version_text}",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print(panel)


if __name__ == "__main__":
    app()
