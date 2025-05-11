"""
Knowledge base tool for querying document knowledge.
"""

import logging

from agents.document_processor import query_knowledge_base
from langchain.tools import BaseTool

logger = logging.getLogger(__name__)


class KnowledgeBaseTool(BaseTool):
    """Tool for querying the knowledge base."""

    name: str = "knowledge_base_query"
    description: str = """Use this tool to query the knowledge base of uploaded documents.
    This is useful when you need to retrieve information from documents that have been uploaded by the user.
    The input should be a natural language query related to the content of the documents.
    """

    def _run(self, query: str) -> str:
        """Run the knowledge base query."""
        try:
            # Query the knowledge base
            results = query_knowledge_base(query)

            if not results:
                return "No relevant information found in the knowledge base."

            # Format the results
            response = "Here's information from the knowledge base:\n\n"
            for i, doc in enumerate(results, 1):
                response += f"Document {i}:\n{doc.page_content}\n\n"

            return response
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return f"Error querying knowledge base: {str(e)}"
