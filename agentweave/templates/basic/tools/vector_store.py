"""
Vector store tool for retrieval augmentation.
"""

import logging
import os
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from .registry import register_tool

logger = logging.getLogger(__name__)

try:
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    VECTOR_STORE_AVAILABLE = True
except ImportError:
    logger.warning(
        "Vector store dependencies not available. Install with 'pip install langchain-openai langchain-chroma'"
    )
    VECTOR_STORE_AVAILABLE = False


class VectorStoreQueryInput(BaseModel):
    """Input schema for the vector store query tool."""

    query: str = Field(
        description="The query to search for in the vector store.",
    )
    k: int = Field(
        default=5,
        description="Number of results to return.",
    )


class VectorStoreAddInput(BaseModel):
    """Input schema for the vector store add tool."""

    text: str = Field(
        description="The text to add to the vector store.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata to associate with the text.",
    )


@register_tool
class VectorStoreQueryTool(BaseTool):
    """Tool for querying a vector store for similar documents."""

    name: str = "vector_store_query"
    description: str = "Query a vector store for documents similar to the input query. Use this when you need to retrieve information from a knowledge base."
    args_schema: type[BaseModel] = VectorStoreQueryInput
    persist_directory: str | None = None
    embedding_model: Any | None = None
    _error_message: str | None = None
    vector_store: Any | None = None

    def __init__(
        self,
        persist_directory: str | None = None,
        embedding_model: Any | None = None,
    ):
        """Initialize the vector store query tool."""
        super().__init__()

        if not VECTOR_STORE_AVAILABLE:
            self._error_message = "Vector store dependencies not available. Install with 'pip install langchain-openai langchain-chroma'"
            return

        self.persist_directory = persist_directory or os.environ.get(
            "VECTOR_STORE_DIR", "./vector_store"
        )

        # Create the directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize embeddings
        self.embedding_model = embedding_model
        if not self.embedding_model:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self._error_message = (
                    "OpenAI API key not set in environment variable OPENAI_API_KEY"
                )
                return
            self.embedding_model = OpenAIEmbeddings(api_key=api_key)

        # Initialize vector store
        try:
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_model,
            )
            self._error_message = None
            logger.info(
                f"Vector store initialized with {self.vector_store._collection.count()} documents"
            )
        except Exception as e:
            self._error_message = f"Error initializing vector store: {str(e)}"
            logger.error(self._error_message)

    def _run(self, query: str, k: int = 5) -> str:
        """Query the vector store for similar documents."""
        if getattr(self, "_error_message", None):
            return f"Error: {self._error_message}"

        try:
            # Perform similarity search
            results = self.vector_store.similarity_search_with_score(query, k=k)

            if not results:
                return "No relevant documents found."

            # Format results
            formatted_results = []
            for i, (doc, score) in enumerate(results):
                metadata = doc.metadata or {}
                formatted_results.append(
                    {
                        "document": doc.page_content,
                        "similarity": float(
                            score
                        ),  # Convert numpy float to Python float for JSON serialization
                        "metadata": metadata,
                    }
                )

            # Return a readable format
            response = "Found the following relevant information:\n\n"
            for i, result in enumerate(formatted_results):
                response += f"{i + 1}. {result['document']}\n"
                if i < len(formatted_results) - 1:
                    response += "\n---\n\n"

            return response

        except Exception as e:
            error_message = f"Error querying vector store: {str(e)}"
            logger.error(error_message)
            return f"Error: {error_message}"


@register_tool
class VectorStoreAddTool(BaseTool):
    """Tool for adding documents to a vector store."""

    name: str = "vector_store_add"
    description: str = "Add text to the vector store knowledge base. Use this when you need to store information for later retrieval."
    args_schema: type[BaseModel] = VectorStoreAddInput
    persist_directory: str | None = None
    embedding_model: Any | None = None
    _error_message: str | None = None
    vector_store: Any | None = None
    text_splitter: Any | None = None

    def __init__(
        self,
        persist_directory: str | None = None,
        embedding_model: Any | None = None,
    ):
        """Initialize the vector store add tool."""
        super().__init__()

        if not VECTOR_STORE_AVAILABLE:
            self._error_message = "Vector store dependencies not available. Install with 'pip install langchain-openai langchain-chroma'"
            return

        self.persist_directory = persist_directory or os.environ.get(
            "VECTOR_STORE_DIR", "./vector_store"
        )

        # Create the directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize embeddings
        self.embedding_model = embedding_model
        if not self.embedding_model:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self._error_message = (
                    "OpenAI API key not set in environment variable OPENAI_API_KEY"
                )
                return
            self.embedding_model = OpenAIEmbeddings(api_key=api_key)

        # Initialize vector store
        try:
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_model,
            )
            self._error_message = None

            # Create text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
            )

            logger.info(
                f"Vector store initialized with {self.vector_store._collection.count()} documents"
            )
        except Exception as e:
            self._error_message = f"Error initializing vector store: {str(e)}"
            logger.error(self._error_message)

    def _run(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        """Add text to the vector store."""
        if getattr(self, "_error_message", None):
            return f"Error: {self._error_message}"

        try:
            # Split the text into chunks
            chunks = self.text_splitter.split_text(text)

            # Prepare documents with metadata
            from langchain_core.documents import Document

            documents = [Document(page_content=chunk, metadata=metadata or {}) for chunk in chunks]

            # Add documents to vector store
            self.vector_store.add_documents(documents)

            # Persist the vector store
            self.vector_store.persist()

            return f"Successfully added {len(documents)} document chunks to the vector store."

        except Exception as e:
            error_message = f"Error adding to vector store: {str(e)}"
            logger.error(error_message)
            return f"Error: {error_message}"


# Example of using the tools
if __name__ == "__main__":
    query_tool = VectorStoreQueryTool()
    add_tool = VectorStoreAddTool()

    # Add some sample text
    sample_text = """
    AgentWeave is a powerful CLI tool for initializing and managing AI agent projects based on LangGraph.
    It helps developers quickly bootstrap AI agent projects with all the necessary components,
    including tools, memory, monitoring, and deployment options.
    """

    result = add_tool.invoke({"text": sample_text, "metadata": {"source": "documentation"}})
    print(result)

    # Query the vector store
    result = query_tool.invoke({"query": "What is AgentWeave?", "k": 3})
    print(result)
