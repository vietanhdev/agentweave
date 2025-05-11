"""
Command to convert an existing project into a template.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from agentweave.utils.template_generator import create_template_from_project

app = typer.Typer(
    name="convert-to-template",
    help="Convert an existing project into a template",
    add_completion=False,
)

console = Console()


@app.callback()
def callback():
    """
    Convert an existing project into a template.
    """
    pass


@app.command()
def main(
    project_dir: str = typer.Argument(..., help="Path to the project directory"),
    template_name: str = typer.Argument(..., help="Name for the new template"),
    exclude: str = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Comma-separated list of patterns to exclude (e.g. '*.pyc,node_modules')",
    ),
):
    """
    Convert an existing project into a template.

    This command takes an existing project and creates a template from it.

    Examples:
        agentweave convert-to-template ./my-project my-custom-template
        agentweave convert-to-template ./my-project my-template --exclude "*.pyc,node_modules"
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        console=console,
    ) as progress:
        task = progress.add_task("Converting project to template...", total=None)

        try:
            # Convert exclude string to list if provided
            exclude_patterns = None
            if exclude:
                exclude_patterns = [pattern.strip() for pattern in exclude.split(",")]

            # Convert the project to a template
            create_template_from_project(
                project_dir=Path(project_dir),
                template_name=template_name,
                exclude_paths=exclude_patterns,
            )

            progress.update(
                task, description="Project converted to template successfully!"
            )

            console.print(
                f"\n[bold green]✓ Project successfully converted to template: {template_name}[/bold green]"
            )
            console.print("\n[cyan]Next steps:[/cyan]")
            console.print(
                "  1. Edit files in the template to replace specific values with placeholders like {{project_name}}"
            )
            console.print(
                "  2. Update the schema.yaml file with appropriate configuration options"
            )
            console.print(
                "  3. Use your new template with: agentweave init my-new-project -t "
                + template_name
            )

        except Exception as e:
            console.print(f"[red]Error converting project to template: {str(e)}[/red]")
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
