"""
Template generator utilities for AgentWeave.

This module provides a declarative configuration-based approach to template generation,
replacing the previous Jinja2 template system with a more maintainable approach.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from agentweave.utils.config import get_package_path


def get_templates_dir() -> Path:
    """Get the path to the templates directory."""
    return get_package_path() / "templates"


class TemplateGenerator:
    """Template generator that uses declarative configuration for template generation."""

    def __init__(self, template_name: str, output_dir: Path, config: dict[str, Any]):
        """
        Initialize the template generator.

        Args:
            template_name: Name of the template to use
            output_dir: Directory where the project will be generated
            config: Configuration parameters for template generation
        """
        self.template_name = template_name
        self.output_dir = output_dir
        self.config = config
        self.templates_dir = get_templates_dir()
        self.template_dir = self.templates_dir / template_name
        self.placeholder_pattern = re.compile(r"{{(\s*)([\w\.]+)(\s*)}}")

        # Set of files to ignore during template processing
        self.ignore_files = {
            ".git",
            ".DS_Store",
            "__pycache__",
            ".pyc",
            "node_modules",
            ".next",
            ".venv",
            ".env",
        }

        # Load template schema if it exists
        self.schema_path = self.template_dir / "schema.yaml"
        self.schema = self._load_schema() if self.schema_path.exists() else {}

        # Validate config against schema
        self._validate_config()

    def _load_schema(self) -> dict[str, Any]:
        """Load and parse the template schema file."""
        with open(self.schema_path) as f:
            return yaml.safe_load(f)

    def _validate_config(self) -> None:
        """Validate the provided configuration against the schema."""
        if not self.schema:
            return

        # Basic validation of required fields
        if "required" in self.schema:
            for field in self.schema["required"]:
                if field not in self.config:
                    raise ValueError(f"Required configuration field '{field}' is missing")

        # Type validation could be added here
        # For now, we'll keep it simple

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if a file should be ignored during template processing."""
        for ignore_pattern in self.ignore_files:
            if ignore_pattern in str(file_path):
                return True
        return False

    def _process_placeholder(self, match) -> str:
        """Process a placeholder match and replace with config value."""
        placeholder = match.group(2).strip()

        # Handle nested properties with dot notation (e.g., "user.name")
        if "." in placeholder:
            parts = placeholder.split(".")
            value = self.config
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    # Return original placeholder if key not found
                    return match.group(0)
            return str(value)

        # Handle simple property lookup
        if placeholder in self.config:
            return str(self.config[placeholder])

        # Return original placeholder if key not found
        return match.group(0)

    def _replace_placeholders(self, content: str) -> str:
        """Replace placeholders in content with values from config."""
        return self.placeholder_pattern.sub(self._process_placeholder, content)

    def _process_file(self, src_file: Path, dst_file: Path) -> None:
        """Process a single file, replacing placeholders with config values."""
        # Check if file is binary or text
        try:
            with open(src_file, encoding="utf-8") as f:
                content = f.read()

            # Replace placeholders in the content
            processed_content = self._replace_placeholders(content)

            # Write processed content to destination
            with open(dst_file, "w", encoding="utf-8") as f:
                f.write(processed_content)

        except UnicodeDecodeError:
            # If we can't decode as UTF-8, assume it's a binary file and copy directly
            shutil.copy2(src_file, dst_file)

    def _process_filename(self, filename: str) -> str:
        """Process filename, replacing placeholders with config values."""
        return self._replace_placeholders(filename)

    def generate(self) -> None:
        """Generate the project from the template."""
        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self.template_name}")

        # Create the output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Walk through the template directory
        for root, dirs, files in os.walk(self.template_dir):
            # Skip schema.yaml at the root level
            if Path(root) == self.template_dir and "schema.yaml" in files:
                files.remove("schema.yaml")

            # Skip any directories in our ignore list
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(d))]

            # Calculate relative path from template directory
            rel_path = Path(root).relative_to(self.template_dir)
            target_dir = self.output_dir / rel_path

            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)

            # Process each file
            for file in files:
                if self._should_ignore_file(Path(file)):
                    continue

                src_file = Path(root) / file

                # Process the filename (may contain placeholders)
                processed_filename = self._process_filename(file)

                # Create destination file path
                dst_file = target_dir / processed_filename

                # Process the file
                self._process_file(src_file, dst_file)


def generate_from_template(
    template_name: str,
    output_dir: Path,
    config: dict[str, Any],
) -> None:
    """
    Generate a project from a template.

    Args:
        template_name: Name of the template to use
        output_dir: Directory where the project will be generated
        config: Configuration parameters for template generation
    """
    generator = TemplateGenerator(template_name, output_dir, config)
    generator.generate()


def create_template_from_project(
    project_dir: Path,
    template_name: str,
    output_dir: Path | None = None,
    exclude_paths: list[str] | None = None,
) -> None:
    """
    Create a template from an existing project.

    Args:
        project_dir: Directory of the existing project
        template_name: Name to give the new template
        output_dir: Directory where the template will be created (defaults to agentweave/templates/{template_name})
        exclude_paths: List of relative paths to exclude from the template
    """
    if not output_dir:
        output_dir = get_templates_dir() / template_name

    # Create template directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Default exclude paths
    if exclude_paths is None:
        exclude_paths = [
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
            ".next",
            ".DS_Store",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".env",
            "dist",
            "build",
        ]

    # Create a simple schema.yaml file
    schema = {
        "description": "Template configuration schema",
        "required": ["project_name", "project_description"],
        "properties": {
            "project_name": {"type": "string", "description": "Name of the project"},
            "project_description": {
                "type": "string",
                "description": "Description of the project",
            },
            # Add more properties as needed
        },
    }

    # Write schema.yaml
    with open(output_dir / "schema.yaml", "w") as f:
        yaml.dump(schema, f, default_flow_style=False)

    # Copy project files to template directory
    for root, dirs, files in os.walk(project_dir):
        # Apply exclusions
        dirs[:] = [d for d in dirs if not any(re.match(pattern, d) for pattern in exclude_paths)]

        # Calculate relative path from project directory
        rel_path = Path(root).relative_to(project_dir)
        target_dir = output_dir / rel_path

        # Skip excluded paths
        if any(re.match(pattern, str(rel_path)) for pattern in exclude_paths):
            continue

        # Create target directory
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy each file
        for file in files:
            src_file = Path(root) / file

            # Skip excluded files
            if any(re.match(pattern, file) for pattern in exclude_paths):
                continue

            # Copy the file to the template directory
            dst_file = target_dir / file
            shutil.copy2(src_file, dst_file)

    print(f"Template '{template_name}' created successfully at: {output_dir}")
    print("Remember to replace specific values with placeholders like {{project_name}}")
