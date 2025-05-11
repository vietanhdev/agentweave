"""
Configuration utilities for AgentWeave.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def is_agentweave_project(path: Optional[Path] = None) -> bool:
    """Check if the given path is an AgentWeave project."""
    path = path or Path.cwd()
    return (path / "agentweave.yaml").exists()


def load_project_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the project configuration."""
    path = path or Path.cwd()
    config_path = path / "agentweave.yaml"

    if not config_path.exists():
        return {}

    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


def save_project_config(config: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Save the project configuration."""
    path = path or Path.cwd()
    config_path = path / "agentweave.yaml"

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_available_templates() -> List[str]:
    """Get a list of available project templates."""
    # Scan the templates directory rather than returning a static list
    templates_dir = get_package_path() / "templates"
    return [
        d.name
        for d in templates_dir.iterdir()
        if d.is_dir() and not d.name.startswith("__")
    ]


def get_available_tools() -> List[str]:
    """Get a list of available tools."""
    # For now, return a static list
    # In the future, this should scan the tools directory
    return [
        "web-search",
        "file-io",
        "calculator",
        "weather",
        "wikipedia",
        "calendar",
        "email",
        "code-interpreter",
        "database",
        "api-connector",
    ]


def get_available_memories() -> List[str]:
    """Get a list of available memory components."""
    # For now, return a static list
    # In the future, this should scan the memory directory
    return [
        "simple",
        "vector-store",
        "conversation",
        "document",
        "redis",
    ]


def get_available_monitors() -> List[str]:
    """Get a list of available monitoring components."""
    # For now, return a static list
    # In the future, this should scan the monitoring directory
    return [
        "tracing",
        "dashboard",
        "metrics",
        "debugger",
        "langfuse",
    ]


def get_package_path() -> Path:
    """Get the path to the AgentWeave package."""
    import agentweave

    return Path(agentweave.__file__).parent
