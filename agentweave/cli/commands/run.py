"""
Command to run an AgentWeave project in development mode.
"""

import atexit
import os
import signal
import subprocess
import sys
from pathlib import Path

import psutil
import typer
from rich.console import Console

from agentweave.utils.config import is_agentweave_project, load_project_config

# Create a command directly rather than a command group
console = Console()

# Global list to track all child processes
_processes = []


def cleanup_processes():
    """Cleanup all tracked processes when the program exits."""
    for proc in _processes:
        try:
            # Check if process is still running
            if proc.poll() is None:
                process = psutil.Process(proc.pid)
                # Kill process and its children
                for child in process.children(recursive=True):
                    try:
                        child.terminate()
                    except Exception:
                        pass
                process.terminate()
                console.print(
                    f"[yellow]Terminated process with PID {proc.pid}[/yellow]"
                )
        except (psutil.NoSuchProcess, ProcessLookupError):
            # Process already terminated
            pass
        except Exception as e:
            console.print(f"[red]Error terminating process: {str(e)}[/red]")


def run_command(
    backend_only: bool = typer.Option(
        False,
        "--backend-only",
        "-b",
        help="Only run the backend server",
    ),
    frontend_only: bool = typer.Option(
        False,
        "--frontend-only",
        "-f",
        help="Only run the frontend server",
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
    reload: bool = typer.Option(
        True,
        "--reload/--no-reload",
        help="Enable/disable auto-reload on file changes",
    ),
    no_install: bool = typer.Option(
        False,
        "--no-install",
        help="Skip installing the package in development mode",
    ),
):
    """
    Run an AgentWeave project in development mode.

    This command runs the backend server (FastAPI) and optionally the frontend server (Next.js if available).

    Examples:
        agentweave run
        agentweave run --backend-only
        agentweave run --frontend-only
        agentweave run --port 8080 --frontend-port 3001
        agentweave run --use-current-env
    """
    # Check if current directory is an AgentWeave project
    if not is_agentweave_project():
        console.print(
            "[red]Not an AgentWeave project. Run this command from the project root.[/red]"
        )
        raise typer.Exit(1)

    # Get project directory
    project_dir = Path.cwd()

    # Get project config
    project_config = load_project_config()
    project_name = project_config.get("name", Path.cwd().name)

    console.print(f"\n[bold cyan]Running {project_name}[/bold cyan]")

    # Remind about environment setup
    env_example_path = project_dir / ".env.example"
    env_local_path = project_dir / ".env"
    if env_example_path.exists() and not env_local_path.exists():
        console.print(
            "\n[yellow]Note: It appears you haven't set up your environment variables yet.[/yellow]"
        )
        console.print(
            f"[yellow]Consider copying {env_example_path} to {env_local_path} and updating the values.[/yellow]"
        )
        console.print(
            "[yellow]This is important for integrating with external services and APIs.[/yellow]\n"
        )

    # Install the package in development mode if not skipped
    if not no_install:
        console.print("[cyan]Installing package in development mode...[/cyan]")
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
            subprocess.run(cmd, check=True, capture_output=True)
            console.print("[green]Package installed successfully[/green]")
        except subprocess.CalledProcessError as e:
            console.print(
                f"[yellow]Warning: Failed to install package: {e.stderr.decode()}[/yellow]"
            )
            console.print(
                "[yellow]You may encounter import errors. Try running 'pip install -e .' manually.[/yellow]"
            )

    # Register process cleanup on exit
    atexit.register(cleanup_processes)

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        console.print(
            "\n[yellow]Received termination signal. Shutting down servers...[/yellow]"
        )
        cleanup_processes()
        console.print("[green]Servers shut down successfully.[/green]")
        sys.exit(0)

    # Set the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Run backend only
        if backend_only:
            console.print("[green]Running backend server only[/green]")
            process = run_backend(project_dir, port, reload)
            if process:
                _processes.append(process)
                process.wait()  # Wait for the backend process to exit
            return

        # Run frontend only
        if frontend_only:
            console.print("[green]Running frontend server only[/green]")
            process = run_frontend(project_dir, frontend_port)
            if process:
                _processes.append(process)
                process.wait()  # Wait for the frontend process to exit
            return

        # Run both backend and frontend
        console.print("[green]Running backend and frontend servers[/green]")
        run_both(project_dir, port, frontend_port, reload)

    except Exception as e:
        console.print(f"[red]Error running project: {str(e)}[/red]")
        raise typer.Exit(1)


def run_backend(project_dir: Path, port: int, reload: bool):
    """Run the backend server."""
    # First try to find the backend directory
    src_backend_dir = project_dir / "src" / "backend"
    backend_dir = project_dir / "backend"

    # Determine the module path based on the directory structure
    if src_backend_dir.exists() and (src_backend_dir / "main.py").exists():
        # Use src.backend.main:app
        module_path = "src.backend.main:app"
    elif backend_dir.exists() and (backend_dir / "main.py").exists():
        # Use backend.main:app
        module_path = "backend.main:app"
    else:
        console.print("[red]Backend directory with main.py not found.[/red]")
        raise typer.Exit(1)

    # Build the command to run the backend server
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        module_path,
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]

    if reload:
        cmd.append("--reload")

    # Run the backend server
    try:
        console.print(f"[bold]Starting backend server on port {port}[/bold]")
        console.print(f"[cyan]API available at: http://localhost:{port}[/cyan]")
        console.print(
            f"[cyan]API docs available at: http://localhost:{port}/docs[/cyan]"
        )
        console.print(f"[dim]Using module: {module_path}[/dim]")

        # Use start_new_session on Unix-like systems to create a new process group
        # This ensures child processes can be properly terminated
        kwargs = {}
        if sys.platform != "win32":
            kwargs["start_new_session"] = True

        # Add PYTHONPATH to ensure the package can be imported
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_dir)

        process = subprocess.Popen(cmd, cwd=str(project_dir), env=env, **kwargs)

        return process

    except subprocess.CalledProcessError as e:
        console.print(
            f"[red]Error starting backend server: {e.stderr.decode() if e.stderr else str(e)}[/red]"
        )
        raise typer.Exit(1)


def run_frontend(project_dir: Path, port: int):
    """Run the frontend server."""
    frontend_dir = project_dir / "frontend"

    # Check if the frontend directory exists
    if not frontend_dir.exists():
        console.print(
            "[red]Frontend directory not found. Cannot run frontend server.[/red]"
        )
        raise typer.Exit(1)

    # Check if package.json exists
    if not (frontend_dir / "package.json").exists():
        console.print(
            "[red]package.json not found in frontend directory. Cannot run frontend server.[/red]"
        )
        raise typer.Exit(1)

    try:
        # Check if yarn.lock exists
        if (frontend_dir / "yarn.lock").exists():
            cmd = ["yarn", "dev"]
        # Check if pnpm-lock.yaml exists
        elif (frontend_dir / "pnpm-lock.yaml").exists():
            cmd = ["pnpm", "dev"]
        # Default to npm
        else:
            cmd = ["npm", "run", "dev"]

        # Add port if provided and not the default
        if port != 3000:
            cmd.extend(["--", "--port", str(port)])

        console.print(f"[bold]Starting frontend server on port {port}[/bold]")
        console.print(f"[cyan]Frontend available at: http://localhost:{port}[/cyan]")

        # Use start_new_session on Unix-like systems to create a new process group
        # This ensures child processes can be properly terminated
        kwargs = {}
        if sys.platform != "win32":
            kwargs["start_new_session"] = True

        # Set environment variables for the frontend process
        env = os.environ.copy()
        backend_port = os.environ.get("BACKEND_PORT", "8000")
        env["BACKEND_URL"] = f"http://localhost:{backend_port}"
        env["NEXT_PUBLIC_BACKEND_URL"] = f"http://localhost:{backend_port}"

        process = subprocess.Popen(cmd, cwd=str(frontend_dir), env=env, **kwargs)

        return process

    except subprocess.CalledProcessError as e:
        console.print(
            f"[red]Error starting frontend server: {e.stderr.decode() if e.stderr else str(e)}[/red]"
        )
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print(
            "[red]Could not find npm, yarn, or pnpm. Please ensure Node.js is installed.[/red]"
        )
        raise typer.Exit(1)


def run_both(project_dir: Path, backend_port: int, frontend_port: int, reload: bool):
    """Run both backend and frontend servers."""
    # Start backend
    backend_process = run_backend(project_dir, backend_port, reload)
    if backend_process:
        _processes.append(backend_process)

    # Start frontend
    try:
        frontend_process = run_frontend(project_dir, frontend_port)
        if frontend_process:
            _processes.append(frontend_process)
    except typer.Exit:
        # If frontend fails, kill backend and exit
        console.print(
            "[yellow]Frontend server failed to start. Backend server is still running.[/yellow]"
        )
        console.print(
            f"[cyan]Access the backend at: http://localhost:{backend_port}[/cyan]"
        )
        console.print(
            f"[cyan]API docs available at: http://localhost:{backend_port}/docs[/cyan]"
        )
        return

    console.print("\n[bold green]✓ Both servers started successfully![/bold green]")
    console.print(f"[cyan]Backend available at: http://localhost:{backend_port}[/cyan]")
    console.print(
        f"[cyan]API docs available at: http://localhost:{backend_port}/docs[/cyan]"
    )
    console.print(
        f"[cyan]Frontend available at: http://localhost:{frontend_port}[/cyan]"
    )
    console.print("\n[yellow]Press Ctrl+C to stop all servers[/yellow]")

    # Wait for processes to complete
    try:
        # Wait for the backend process specifically
        if backend_process:
            backend_process.wait()
    except KeyboardInterrupt:
        # This shouldn't actually be reached because of our signal handler,
        # but just in case...
        console.print("\n[yellow]Shutting down servers...[/yellow]")
        cleanup_processes()
        console.print("[green]Servers shut down successfully.[/green]")


# Export the command as app
app = run_command
