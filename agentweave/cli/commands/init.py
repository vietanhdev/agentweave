"""
Command to initialize a new AgentWeave project.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from agentweave.utils.config import get_available_templates
from agentweave.utils.template_generator import (
    generate_from_template,
    get_templates_dir,
)

# Create a single command function
console = Console()


def init_command(
    project_name: str = typer.Argument(..., help="Name of the project"),
    template: str = typer.Option(
        "basic",
        "--template",
        "-t",
        help="Template to use for the project",
    ),
    skip_prompts: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip all prompts and use defaults",
    ),
):
    """
    Initialize a new AgentWeave project.

    Examples:
        agentweave init {{project_name}}
        agentweave init {{project_name}} --template conversational
        agentweave init {{project_name}} -t basic -y
    """
    console.print(
        f"\n[bold cyan]Creating new AgentWeave project: [/bold cyan][bold white]{project_name}[/bold white]"
    )

    # Check if directory exists
    project_dir = Path(project_name)
    if project_dir.exists():
        if skip_prompts or Confirm.ask(
            f"Directory {project_name} already exists. Continue anyway?",
            default=False,
        ):
            console.print("[yellow]Using existing directory.[/yellow]")
        else:
            console.print("[red]Aborting.[/red]")
            raise typer.Exit(1)
    else:
        project_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Created project directory: {project_name}[/green]")

    # Validate template
    available_templates = get_available_templates()
    if template not in available_templates:
        console.print(
            f"[red]Template '{template}' not found. Available templates:[/red]"
        )
        for t in available_templates:
            console.print(f"  - {t}")
        raise typer.Exit(1)

    # Get project configuration settings
    config = {
        "project_name": project_name,
        "project_description": "An AI agent built with AgentWeave",
        "author": "",
    }

    if not skip_prompts:
        config["project_description"] = Prompt.ask(
            "Project description",
            default=config["project_description"],
        )
        config["author"] = Prompt.ask(
            "Author",
            default="",
        )

    # Check if .env.example exists in the template and prompt for values
    templates_dir = get_templates_dir()
    template_dir = templates_dir / template
    env_example_path = template_dir / ".env.example"

    env_vars = {}
    if env_example_path.exists() and not skip_prompts:
        console.print("\n[cyan]Setting up environment variables:[/cyan]")

        with open(env_example_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, default_value = line.split("=", 1)
                    key = key.strip()
                    default_value = default_value.strip()

                    # If value is in quotes, remove them
                    if (
                        default_value
                        and default_value[0] in ('"', "'")
                        and default_value[-1] == default_value[0]
                    ):
                        default_value = default_value[1:-1]

                    value = Prompt.ask(
                        f"Enter value for {key}",
                        default=default_value,
                    )
                    env_vars[key] = value

    # Initialize project using the template generator
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing project...", total=None)

        try:
            # Generate the project from the template using our new generator
            generate_from_template(
                template_name=template,
                output_dir=project_dir,
                config=config,
            )

            # Write the .env file if we collected env vars
            if env_vars:
                env_path = project_dir / ".env"
                with open(env_path, "w") as f:
                    for key, value in env_vars.items():
                        f.write(f"{key}={value}\n")

                console.print("[green]Environment variables saved to .env file[/green]")

            progress.update(task, description="Project initialized successfully!")

            console.print(
                "\n[bold green]✓ Project initialized successfully![/bold green]"
            )
            console.print("\n[cyan]To get started:[/cyan]")
            console.print(f"  cd {project_name}")
            console.print("  agentweave install_env")
            console.print("  agentweave run")
            console.print(
                "\n[cyan]For more information, see the README.md file in your project directory.[/cyan]"
            )

        except Exception as e:
            console.print(f"[red]Error initializing project: {str(e)}[/red]")
            raise typer.Exit(1)


# Export the command as app
app = init_command
