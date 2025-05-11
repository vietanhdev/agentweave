"""
{{project_name}} - Backend Server

This is the main entry point for the FastAPI backend server.
"""

import logging
from typing import Any, Dict, Optional

# Import the agent
from agents.agent import create_agent, invoke_agent

# Import routers - use absolute imports
from backend.routers import agent, tools, documents
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="{{project_name}} API",
    description="An AI agent built with AgentWeave",
    version="0.1.0",
)

# Configure CORS - Most permissive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)

# Include routers
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])


class QueryRequest(BaseModel):
    """Request model for agent queries."""

    query: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """Response model for agent queries."""

    response: str
    conversation_id: str
    metadata: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """Root endpoint returning basic information."""
    return {
        "name": "{{project_name}}",
        "description": "An AI agent built with AgentWeave",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a query using the LangGraph agent.
    """
    try:
        # Create or get the agent for this conversation
        agent = create_agent(request.conversation_id)

        # Invoke the agent with the query
        result = invoke_agent(
            agent=agent,
            query=request.query,
            conversation_id=request.conversation_id,
            context=request.context or {},
        )

        return {
            "response": result["response"],
            "conversation_id": result["conversation_id"],
            "metadata": result.get("metadata", {}),
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
