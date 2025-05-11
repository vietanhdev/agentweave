"""
Router for agent-related endpoints.
"""

import logging
from typing import Any, Dict, Optional

from agents.agent import create_agent, get_agent_config
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentConfig(BaseModel):
    """Model for agent configuration."""

    llm_provider: str
    model: str
    temperature: float
    max_tokens: Optional[int] = None
    other_params: Optional[Dict[str, Any]] = None


@router.get("/config")
async def get_config():
    """Get agent configuration."""
    try:
        config = get_agent_config()
        return config
    except Exception as e:
        logger.error(f"Error getting agent config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset/{conversation_id}")
async def reset_conversation(conversation_id: str):
    """Reset a conversation."""
    try:
        # Create a new agent (which will reset the conversation state)
        create_agent(conversation_id, reset=True)
        return {
            "status": "ok",
            "message": f"Conversation {conversation_id} reset successfully",
        }
    except Exception as e:
        logger.error(f"Error resetting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def list_conversations():
    """List active conversations."""
    # This would need to be implemented in the agent module
    # For now, return a placeholder
    return {"conversations": []}
