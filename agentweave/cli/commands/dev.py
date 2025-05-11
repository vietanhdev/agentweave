"""
Command to set up and run development tools for an AgentWeave project.
"""

import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentweave.cli.commands.install_env import install_env
from agentweave.cli.commands.run import run_command as run_project
from agentweave.utils.config import is_agentweave_project, load_project_config

console = Console()


def dev_command(
    watch: bool = typer.Option(
        True,
        "--watch/--no-watch",
        help="Watch for changes and auto-reload",
    ),
    lint: bool = typer.Option(
        False,
        "--lint",
        "-l",
        help="Run linting tools",
    ),
    test: bool = typer.Option(
        False,
        "--test",
        "-t",
        help="Run unit tests",
    ),
    format: bool = typer.Option(
        False,
        "--format",
        "-f",
        help="Format code using black and isort",
    ),
    check: bool = typer.Option(
        False,
        "--check",
        "-c",
        help="Run all checks (lint, test, and type checking)",
    ),
    install: bool = typer.Option(
        False,
        "--install",
        "-i",
        help="Install development dependencies",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port for the backend server",
    ),
    frontend_port: int = typer.Option(
        3000,
        "--frontend-port",
        "-fp",
        help="Port for the frontend server",
    ),
):
    """
    Run development tools for an AgentWeave project.

    This command provides a unified interface for development tasks such as:
    - Running the project with hot reloading
    - Linting code
    - Running tests
    - Formatting code
    - Type checking

    Examples:
        agentweave dev               # Run the project with hot reloading
        agentweave dev --lint        # Run linters
        agentweave dev --test        # Run tests
        agentweave dev --format      # Format code
        agentweave dev --check       # Run all checks
        agentweave dev --install     # Install dev dependencies
    """
    # Check if we're in an AgentWeave project
    if not is_agentweave_project():
        console.print(
            "[red]Not in an AgentWeave project. Please run this command in the root of an AgentWeave project.[/red]"
        )
        raise typer.Exit(1)

    project_config = load_project_config()
    project_name = project_config.get("name", "AgentWeave project")

    console.print(
        f"\n[bold cyan]Development tools for: [/bold cyan][bold white]{project_name}[/bold white]"
    )

    # Install development dependencies if requested
    if install:
        console.print("\n[bold]Installing development dependencies...[/bold]")
        # Use the existing install_env command with dev=True
        install_env(force=False, skip_frontend=False, dev=True)

    # Get project root directory
    project_dir = Path.cwd()

    # If any specific tool was requested, run it
    if lint or test or format or check:
        if check:
            run_checks(project_dir)
        if test:
            run_tests(project_dir)
        return

    # If no specific tool was requested, run the project
    if watch:
        show_dev_dashboard(project_dir)
        # Run the project with hot reloading - explicitly pass all parameters
        run_project(
            backend_only=False,
            frontend_only=False,
            port=port,
            frontend_port=frontend_port,
            reload=True,
        )
    else:
        # Run without hot reloading - explicitly pass all parameters
        run_project(
            backend_only=False,
            frontend_only=False,
            port=port,
            frontend_port=frontend_port,
            reload=False,
        )


def show_dev_dashboard(project_dir: Path):
    """Display a dashboard with useful development information."""
    # Gather project info
    templates_dir = project_dir / "templates" if (project_dir / "templates").exists() else None
    frontend_dir = project_dir / "frontend" if (project_dir / "frontend").exists() else None
    backend_dir = project_dir / "backend" if (project_dir / "backend").exists() else None
    test_dir = project_dir / "tests" if (project_dir / "tests").exists() else None

    panel = Panel(
        "[bold blue]AgentWeave Development Dashboard[/bold blue]\n\n"
        "[cyan]Commands:[/cyan]\n"
        "  - [green]lint[/green]: Run linters (agentweave dev --lint)\n"
        "  - [green]test[/green]: Run tests (agentweave dev --test)\n"
        "  - [green]format[/green]: Format code (agentweave dev --format)\n"
        "  - [green]check[/green]: Run all checks (agentweave dev --check)\n\n"
        "[cyan]Project Structure:[/cyan]",
        title="Development Mode",
        border_style="cyan",
    )
    console.print(panel)

    # Print project structure table
    table = Table(title="Project Components")
    table.add_column("Component", style="bold cyan")
    table.add_column("Status", style="green")
    table.add_column("Path", style="blue")

    table.add_row(
        "Backend",
        "✓" if backend_dir else "✗",
        str(backend_dir) if backend_dir else "Not found",
    )
    table.add_row(
        "Frontend",
        "✓" if frontend_dir else "✗",
        str(frontend_dir) if frontend_dir else "Not found",
    )
    table.add_row(
        "Templates",
        "✓" if templates_dir else "✗",
        str(templates_dir) if templates_dir else "Not found",
    )
    table.add_row("Tests", "✓" if test_dir else "✗", str(test_dir) if test_dir else "Not found")

    console.print(table)
    console.print("\n[yellow]Starting development server with hot reloading...[/yellow]\n")


def run_tests(project_dir: Path):
    """Run tests on the project."""
    console.print("\n[bold]Running tests...[/bold]")

    # Check if pytest is available
    try:
        subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            capture_output=True,
            check=False,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        console.print("[yellow]pytest not found. Install it to run tests.[/yellow]")
        return

    # Determine test directory or files
    test_dir = project_dir / "tests"
    test_path = str(test_dir) if test_dir.exists() else "."

    # Run pytest
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_path, "-v"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            check=False,
        )
        if result.returncode != 0:
            console.print("[red]Tests failed:[/red]")
            console.print(result.stdout)
        else:
            console.print("[green]All tests passed![/green]")
            console.print(result.stdout)
    except Exception as e:
        console.print(f"[red]Error running tests: {str(e)}[/red]")


def run_checks(project_dir: Path):
    """Run all checks: testing, and formatting."""
    run_tests(project_dir)


# Export the command as app
app = dev_command
