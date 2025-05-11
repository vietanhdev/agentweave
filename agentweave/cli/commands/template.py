"""
Template management commands for the AgentWeave CLI.
"""

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from agentweave.utils.template_generator import (
    create_template_from_project,
    get_templates_dir,
)

app = typer.Typer(help="Manage project templates")
console = Console()


@app.command("create")
def create_template(
    project_dir: str = typer.Argument(
        ..., help="Path to the project directory to create a template from"
    ),
    template_name: str = typer.Argument(..., help="Name for the new template"),
    exclude: list[str] | None = typer.Option(
        None, "--exclude", "-e", help="Patterns to exclude from the template"
    ),
):
    """Create a new template from an existing project."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating template...", total=1)

        try:
            project_path = Path(project_dir).resolve()
            if not project_path.exists():
                console.print(f"[red]Error: Project directory {project_dir} not found[/red]")
                raise typer.Exit(1)

            create_template_from_project(
                project_dir=project_path,
                template_name=template_name,
                exclude_paths=exclude,
            )

            progress.update(task, completed=1, description="Template created successfully!")

            console.print(
                f"\n[bold green]✓ Template '{template_name}' created successfully![/bold green]"
            )
            console.print("\n[cyan]Now update the template by:[/cyan]")
            console.print(f"  1. Edit files in {get_templates_dir() / template_name}")
            console.print(
                "  2. Replace project-specific values with placeholders like {{project_name}}"
            )
            console.print("  3. Update schema.yaml with appropriate configuration options")

        except Exception as e:
            console.print(f"[red]Error creating template: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command("list")
def list_templates():
    """List available templates."""
    templates_dir = get_templates_dir()
    templates = [d.name for d in templates_dir.iterdir() if d.is_dir()]

    if not templates:
        console.print("[yellow]No templates found.[/yellow]")
        return

    console.print("[bold]Available templates:[/bold]")
    for template in sorted(templates):
        console.print(f"  • {template}")


@app.command("info")
def template_info(
    template_name: str = typer.Argument(..., help="Name of the template to show info for"),
):
    """Show information about a template."""
    templates_dir = get_templates_dir()
    template_dir = templates_dir / template_name

    if not template_dir.exists():
        console.print(f"[red]Template '{template_name}' not found[/red]")
        raise typer.Exit(1)

    # Check if the template has a schema.yaml file
    schema_path = template_dir / "schema.yaml"

    console.print(f"[bold]Template:[/bold] {template_name}")

    if schema_path.exists():
        import yaml

        with open(schema_path) as f:
            schema = yaml.safe_load(f)

        if "description" in schema:
            console.print(f"[bold]Description:[/bold] {schema['description']}")

        if "required" in schema:
            console.print("\n[bold]Required configuration:[/bold]")
            for field in schema["required"]:
                description = ""
                if "properties" in schema and field in schema["properties"]:
                    if "description" in schema["properties"][field]:
                        description = f" - {schema['properties'][field]['description']}"
                console.print(f"  • {field}{description}")

        if "properties" in schema:
            optional_props = [
                p
                for p in schema["properties"]
                if "required" not in schema or p not in schema["required"]
            ]

            if optional_props:
                console.print("\n[bold]Optional configuration:[/bold]")
                for field in optional_props:
                    description = ""
                    if "description" in schema["properties"][field]:
                        description = f" - {schema['properties'][field]['description']}"
                    console.print(f"  • {field}{description}")
    else:
        console.print("[yellow]No schema.yaml found for this template.[/yellow]")

    # List files in the template
    console.print("\n[bold]Template structure:[/bold]")
    for root, _dirs, files in os.walk(template_dir):
        level = root.replace(str(template_dir), "").count(os.sep)
        indent = "  " * level
        rel_path = os.path.relpath(root, template_dir)

        if rel_path != ".":
            console.print(f"{indent}• {os.path.basename(root)}/")

        sub_indent = "  " * (level + 1)
        for file in sorted(files):
            if file != "schema.yaml":  # Skip schema file as we've already processed it
                console.print(f"{sub_indent}◦ {file}")
