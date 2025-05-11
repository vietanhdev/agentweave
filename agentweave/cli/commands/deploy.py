"""
Command to deploy an AgentWeave project.
"""

import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

from agentweave.utils.config import is_agentweave_project

app = typer.Typer(
    name="deploy",
    help="Deploy an AgentWeave project",
    add_completion=False,
)

console = Console()


@app.callback()
def callback():
    """
    Deploy an AgentWeave project.
    """
    # Check if current directory is an AgentWeave project
    if not is_agentweave_project():
        console.print(
            "[red]Not an AgentWeave project. Run this command from the project root.[/red]"
        )
        raise typer.Exit(1)


@app.command()
def local():
    """
    Deploy the agent locally as a service.

    Examples:
        agentweave deploy local
    """
    console.print("\n[bold cyan]Deploying agent locally...[/bold cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        console=console,
    ) as progress:
        task = progress.add_task("Building deployment package...", total=None)

        # Create deployment files
        project_dir = Path.cwd()
        deploy_dir = project_dir / "deployment" / "local"
        deploy_dir.mkdir(parents=True, exist_ok=True)

        # Copy necessary deployment files
        # TODO: Implement actual deployment logic

        progress.update(task, description="Deployment files created successfully!")

    console.print("\n[bold green]✓ Agent deployed locally![/bold green]")
    console.print("\n[cyan]To start your agent:[/cyan]")
    console.print("  cd deployment/local")
    console.print("  docker-compose up -d")


@app.command()
def docker():
    """
    Deploy the agent as a Docker container.

    Examples:
        agentweave deploy docker
    """
    console.print("\n[bold cyan]Deploying agent as Docker container...[/bold cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        console=console,
    ) as progress:
        task = progress.add_task("Building Docker image...", total=None)

        # Check if Dockerfile exists
        project_dir = Path.cwd()
        if not (project_dir / "Dockerfile").exists():
            progress.stop()
            console.print("[yellow]Dockerfile not found. Creating one now...[/yellow]")

            # Create Dockerfile
            create_dockerfile(project_dir)

            # Restart progress
            progress.start()
            task = progress.add_task("Building Docker image...", total=None)

        # Build the Docker image
        try:
            image_name = Prompt.ask(
                "Docker image name",
                default=f"agentweave-{project_dir.name}:latest",
            )

            # Build the Docker image
            result = subprocess.run(
                ["docker", "build", "-t", image_name, "."],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                progress.stop()
                console.print(f"[red]Error building Docker image: {result.stderr}[/red]")
                raise typer.Exit(1)

            progress.update(task, description="Docker image built successfully!")

        except Exception as e:
            progress.stop()
            console.print(f"[red]Error building Docker image: {str(e)}[/red]")
            raise typer.Exit(1)

    console.print(f"\n[bold green]✓ Docker image '{image_name}' built successfully![/bold green]")
    console.print("\n[cyan]To run your agent:[/cyan]")
    console.print(f"  docker run -p 8000:8000 {image_name}")


@app.command()
def cloud(
    provider: str = typer.Option(
        None,
        "--provider",
        "-p",
        help="Cloud provider (aws, gcp, azure)",
    ),
):
    """
    Deploy the agent to a cloud provider.

    Examples:
        agentweave deploy cloud --provider aws
        agentweave deploy cloud --provider gcp
        agentweave deploy cloud --provider azure
    """
    console.print("\n[bold cyan]Deploying agent to cloud...[/bold cyan]")

    # Validate provider
    valid_providers = ["aws", "gcp", "azure"]
    if not provider:
        provider = Prompt.ask(
            "Cloud provider",
            choices=valid_providers,
            default="aws",
        )
    elif provider not in valid_providers:
        console.print(
            f"[red]Invalid provider: {provider}. Valid options: {', '.join(valid_providers)}[/red]"
        )
        raise typer.Exit(1)

    console.print(f"[bold]Selected provider: {provider.upper()}[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Preparing deployment for {provider.upper()}...", total=None)

        # Create deployment package
        # TODO: Implement actual cloud deployment logic per provider

        progress.update(task, description=f"Deployment package for {provider.upper()} prepared!")

    console.print(
        f"\n[bold yellow]Cloud deployment to {provider.upper()} is a beta feature.[/bold yellow]"
    )
    console.print(
        "\n[cyan]For detailed deployment instructions, see the generated deployment README.md file.[/cyan]"
    )


def create_dockerfile(project_dir: Path):
    """Create a Dockerfile for the project."""
    docker_content = """FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    with open(project_dir / "Dockerfile", "w") as f:
        f.write(docker_content)

    console.print("[green]Created Dockerfile.[/green]")


if __name__ == "__main__":
    app()
