"""
Template utilities for AgentWeave.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict

import jinja2

from agentweave.utils.config import get_package_path


def get_templates_dir() -> Path:
    """Get the path to the templates directory."""
    return get_package_path() / "templates"


def render_template_string(template_string: str, context: Dict[str, Any]) -> str:
    """Render a template string with the given context."""
    template = jinja2.Template(template_string)
    return template.render(**context)


def render_template_file(
    template_filename: str,
    output_path: Path,
    context: Dict[str, Any],
) -> None:
    """Render a template file with the given context."""
    templates_dir = get_templates_dir()
    template_path = templates_dir / template_filename

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_filename}")

    # Create parent directories if they don't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Render the template
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_filename)
    rendered = template.render(**context)

    # Write the rendered template to the output file
    with open(output_path, "w") as f:
        f.write(rendered)


def copy_template_dir(
    template_name: str,
    output_dir: Path,
    context: Dict[str, Any],
) -> None:
    """Copy a template directory to the output directory."""
    templates_dir = get_templates_dir()
    template_dir = templates_dir / template_name

    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory not found: {template_name}")

    # Create the output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy template files and render Jinja templates
    for root, _, files in os.walk(template_dir):
        rel_path = Path(root).relative_to(template_dir)
        target_dir = output_dir / rel_path
        target_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            src_file = Path(root) / file

            # Skip hidden files
            if file.startswith("."):
                continue

            # Process file name (may contain template variables)
            dest_filename = render_template_string(file, context)

            # Remove .jinja2 extension if present
            if dest_filename.endswith(".jinja2"):
                dest_filename = dest_filename[:-7]

            dest_file = target_dir / dest_filename

            # If the file is a Jinja template, render it
            if file.endswith(".jinja2"):
                with open(src_file, "r") as f:
                    template_content = f.read()

                rendered_content = render_template_string(template_content, context)

                with open(dest_file, "w") as f:
                    f.write(rendered_content)
            else:
                # Otherwise, just copy the file
                shutil.copy2(src_file, dest_file)
