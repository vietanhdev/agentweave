"""
Router for tool-related endpoints.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import tools registry
from tools.registry import _tools, get_tools_schema, toggle_tool

logger = logging.getLogger(__name__)

router = APIRouter()


class ToolSchema(BaseModel):
    """Model for tool schema."""

    name: str
    description: str
    parameters: dict[str, Any]
    required_parameters: list[str]


class ToolToggleRequest(BaseModel):
    """Model for toggling a tool."""

    enabled: bool


@router.get("/")
async def list_tools():
    """List all available tools."""
    try:
        # Use get_tools_schema instead of get_available_tools to get serializable dictionaries
        tools = get_tools_schema()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug")
async def debug_tools():
    """Debug endpoint to show the raw tools dictionary."""
    try:
        # Get the raw _tools dictionary keys
        tools_dict = list(_tools.keys())
        return {"registered_tools": tools_dict}
    except Exception as e:
        logger.error(f"Error getting debug tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{tool_name}/toggle")
async def update_tool_status(tool_name: str, toggle_request: ToolToggleRequest):
    """Toggle a tool's enabled/disabled status."""
    try:
        # Log the current tools dictionary for debugging
        logger.info(f"Current tools in registry: {list(_tools.keys())}")

        success = toggle_tool(tool_name, toggle_request.enabled)
        if not success:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        return {
            "status": "success",
            "tool": tool_name,
            "enabled": toggle_request.enabled,
        }
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Error toggling tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tool_name}/execute")
async def execute_tool(tool_name: str, parameters: dict[str, Any]):
    """Execute a tool with the given parameters."""
    try:
        # This would need to be implemented in the tools registry
        # For now, return a placeholder
        return {
            "status": "ok",
            "tool": tool_name,
            "result": f"Executed {tool_name} with parameters: {parameters}",
        }
    except Exception as e:
        logger.error(f"Error executing tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
