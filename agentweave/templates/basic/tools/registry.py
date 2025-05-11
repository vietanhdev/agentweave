"""
Tool registry for {{project_name}}.

This module provides a central registry for all tools available to the agent.
"""

import importlib
import inspect
import logging
import os
import pkgutil
from typing import Any, Dict, List, Optional, Type

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

# Global registry of available tools
_tools = {}
# Track enabled/disabled state of tools
_tools_enabled = {}
# Map from instance names to class names
_name_to_class_map = {}


def register_tool(tool_class: Type[BaseTool]) -> Type[BaseTool]:
    """
    Register a tool class in the global registry.

    This function can be used as a decorator or called directly.
    """
    # Handle tool name access correctly
    class_name = tool_class.__name__
    instance_name = None

    # Try to get the instance name
    if hasattr(tool_class, "name"):
        if isinstance(tool_class.name, property):
            # If name is a property, try to get its value from a dummy instance
            try:
                dummy = tool_class()
                instance_name = dummy.name
            except Exception:
                instance_name = None
        else:
            instance_name = tool_class.name

    # Use the class name as the key for the tools registry
    _tools[class_name] = tool_class

    # New tools are enabled by default
    if class_name not in _tools_enabled:
        _tools_enabled[class_name] = True

    # Map instance name to class name if available
    if instance_name:
        _name_to_class_map[instance_name] = class_name
        logger.info(
            f"Mapped instance name '{instance_name}' to class name '{class_name}'"
        )

    logger.info(f"Registered tool: {class_name}")
    return tool_class


def get_available_tools() -> List[BaseTool]:
    """
    Get all available tools.

    Returns:
        A list of BaseTool instances of enabled tools only
    """
    _load_tools()

    tools = []

    # Import all tools and add them to the list if enabled
    for class_name, tool_class in _tools.items():
        if _tools_enabled.get(class_name, True):  # Only include enabled tools
            try:
                tools.append(tool_class())
                logger.info(f"Added tool: {class_name}")
            except Exception as e:
                logger.error(f"Error loading tool {class_name}: {str(e)}")

    return tools


def get_tools_schema() -> List[Dict[str, Any]]:
    """
    Get a list of all registered tools with their schemas.
    """
    # Load all tools from the tools directory
    _load_tools()

    tools_list = []
    for class_name, tool_class in _tools.items():
        try:
            # Create an instance to get the schema
            tool_instance = tool_class()

            # Make sure required attributes exist
            if not hasattr(tool_instance, "name") or not tool_instance.name:
                logger.warning(f"Tool {class_name} missing name attribute, skipping")
                continue

            if not hasattr(tool_instance, "description"):
                logger.warning(
                    f"Tool {class_name} missing description, using class name"
                )
                description = class_name
            else:
                description = tool_instance.description

            # Extract parameters schema
            if hasattr(tool_instance, "args_schema") and tool_instance.args_schema:
                try:
                    parameters = tool_instance.args_schema.schema()
                    required_parameters = parameters.get("required", [])
                except Exception as e:
                    logger.warning(f"Could not extract schema for {class_name}: {e}")
                    parameters = {}
                    required_parameters = []
            else:
                parameters = {}
                required_parameters = []

            # Update the name map (in case it wasn't done during registration)
            instance_name = tool_instance.name
            if instance_name and instance_name not in _name_to_class_map:
                _name_to_class_map[instance_name] = class_name
                logger.info(f"Added mapping from '{instance_name}' to '{class_name}'")

            # Extract tool schema and add enabled status
            schema = {
                "name": instance_name,
                "description": description,
                "parameters": parameters,
                "required_parameters": required_parameters,
                "enabled": _tools_enabled.get(class_name, True),
            }

            tools_list.append(schema)
        except Exception as e:
            logger.error(f"Error loading tool {class_name}: {str(e)}")

    logger.info(f"Available tools: {[t['name'] for t in tools_list]}")
    return tools_list


def get_tool_by_name(
    name: str, config: Optional[Dict[str, Any]] = None
) -> Optional[BaseTool]:
    """
    Get a tool instance by name with optional configuration.
    """
    # Load all tools from the tools directory
    _load_tools()

    # Try to get the class name from instance name or use as is
    class_name = _name_to_class_map.get(name, name)

    if class_name not in _tools:
        logger.warning(
            f"Tool {class_name} not found in registry. Available tools: {list(_tools.keys())}"
        )
        return None

    try:
        # Create the tool instance
        tool_class = _tools[class_name]

        if config:
            # Initialize with config
            return tool_class(**config)
        else:
            # Initialize with defaults
            return tool_class()
    except Exception as e:
        logger.error(f"Error creating tool {name}: {str(e)}")
        return None


def toggle_tool(tool_name: str, enabled: bool) -> bool:
    """
    Toggle a tool's enabled/disabled state.

    Args:
        tool_name: The name of the tool to toggle
        enabled: Whether to enable or disable the tool

    Returns:
        True if successful, False otherwise
    """
    # Load all tools from the tools directory
    _load_tools()

    # Log the current tools for debugging
    logger.info(f"Current tools in toggle_tool: {list(_tools.keys())}")
    logger.info(f"Current name map: {_name_to_class_map}")

    # First try direct lookup in name map
    if tool_name in _name_to_class_map:
        class_name = _name_to_class_map[tool_name]
        _tools_enabled[class_name] = enabled
        logger.info(
            f"Tool {class_name} (instance name: {tool_name}) {'enabled' if enabled else 'disabled'}"
        )
        return True

    # Try case-insensitive lookup using the lowercase mapping we added
    tool_name_lower = tool_name.lower()
    if tool_name_lower in _name_to_class_map:
        class_name = _name_to_class_map[tool_name_lower]
        _tools_enabled[class_name] = enabled
        logger.info(
            f"Tool {class_name} (instance name similar to: {tool_name}) {'enabled' if enabled else 'disabled'}"
        )
        return True

    # Then try direct match with tool class names
    if tool_name in _tools:
        _tools_enabled[tool_name] = enabled
        logger.info(f"Tool {tool_name} {'enabled' if enabled else 'disabled'}")
        return True

    # If still not found, try a case-insensitive match with class names
    for class_name in _tools.keys():
        if class_name.lower() == tool_name.lower():
            _tools_enabled[class_name] = enabled
            logger.info(
                f"Tool {class_name} {'enabled' if enabled else 'disabled'} (matched from {tool_name})"
            )
            return True

    # Tool not found
    logger.warning(
        f"Tool {tool_name} not found in registry or name map. Available tools: {list(_tools.keys())}"
    )
    logger.warning(f"Available mappings: {_name_to_class_map}")
    return False


def _load_tools():
    """
    Load all tool modules from the tools directory.
    """
    if _tools:
        # Already loaded
        logger.debug(f"Tools already loaded: {list(_tools.keys())}")
        return

    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Loading tools from directory: {current_dir}")

    # Import all modules in the tools directory
    modules_found = list(pkgutil.iter_modules([current_dir]))
    logger.info(f"Found modules: {[name for _, name, _ in modules_found]}")

    for _, name, is_pkg in modules_found:
        if name != "registry" and not name.startswith("_"):
            try:
                logger.info(f"Attempting to import module: tools.{name}")
                module = importlib.import_module(f"tools.{name}")

                # Find all tool classes in the module
                tool_classes_found = []
                for attr_name, attr_value in module.__dict__.items():
                    if (
                        inspect.isclass(attr_value)
                        and issubclass(attr_value, BaseTool)
                        and attr_value != BaseTool
                    ):
                        # Register the tool
                        register_tool(attr_value)
                        tool_classes_found.append(attr_name)

                if tool_classes_found:
                    logger.info(
                        f"Registered tool classes from {name}: {tool_classes_found}"
                    )
                else:
                    logger.warning(f"No tool classes found in module {name}")

            except Exception as e:
                logger.error(f"Error loading tool module {name}: {str(e)}")
                # Print the full traceback for debugging
                import traceback

                logger.error(traceback.format_exc())

    # After all modules are imported, initialize each tool once to ensure name mappings
    for class_name, tool_class in list(_tools.items()):
        try:
            instance = tool_class()
            if hasattr(instance, "name"):
                instance_name = instance.name
                if instance_name:
                    _name_to_class_map[instance_name] = class_name
                    # Also map the lowercase version for case-insensitive lookups
                    _name_to_class_map[instance_name.lower()] = class_name
                    logger.info(
                        f"Added mapping from instance name '{instance_name}' to class name '{class_name}'"
                    )
        except Exception as e:
            logger.warning(
                f"Error initializing tool {class_name} for name mapping: {str(e)}"
            )

    logger.info(f"Finished loading tools. Available tools: {list(_tools.keys())}")
    logger.info(f"Name to class mappings: {_name_to_class_map}")


# Try to load tools on module import
_load_tools()
