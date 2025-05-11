"""
Configuration utilities for the backend.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the project configuration from the agentweave.yaml file.
    """
    if config_path is None:
        # Try to find the config file in the project root
        project_root = Path(__file__).resolve().parents[2]
        config_path = project_root / "agentweave.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def get_env_var(name: str, default: Optional[str] = None) -> str:
    """
    Get an environment variable with an optional default value.
    """
    value = os.environ.get(name, default)
    if value is None:
        raise ValueError(f"Environment variable {name} not set and no default provided")
    return value


def get_llm_config() -> Dict[str, Any]:
    """
    Get the LLM configuration from the environment or config file.
    """
    # Try to load from config file first
    try:
        config = load_config()
        llm_config = config.get("agent", {})
    except Exception:
        llm_config = {}

    # Override with environment variables if set
    if os.environ.get("LLM_PROVIDER"):
        llm_config["llm_provider"] = os.environ.get("LLM_PROVIDER")

    if os.environ.get("LLM_MODEL"):
        llm_config["model"] = os.environ.get("LLM_MODEL")

    if os.environ.get("LLM_TEMPERATURE"):
        llm_config["temperature"] = float(os.environ.get("LLM_TEMPERATURE"))

    return llm_config
