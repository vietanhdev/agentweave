"""
Document processing module for handling knowledge base documents.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from langchain_community.document_loaders import (
    CSVLoader,
    PDFMinerLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Default documents directory
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documents")

# Metadata database (in-memory for now, could be replaced with a real database)
DOCUMENT_METADATA = {}


def get_loader_for_file(file_path: str):
    """Get the appropriate loader for a file based on its extension."""
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == ".pdf":
        return PDFMinerLoader(file_path)
    elif file_ext == ".csv":
        return CSVLoader(file_path)
    elif file_ext == ".md":
        return UnstructuredMarkdownLoader(file_path)
    else:
        # Default to text loader for .txt and other files
        return TextLoader(file_path)


def process_document(file_path: str) -> Tuple[List[Document], Dict[str, Any]]:
    """
    Process a document file into a list of Documents and return processing metadata.

    Returns:
        Tuple containing:
        - List of Document objects
        - Dictionary with processing metadata (success, chunk_count, etc.)
    """
    stats = {
        "success": False,
        "chunk_count": 0,
        "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        "processing_timestamp": datetime.now().isoformat(),
        "file_name": os.path.basename(file_path),
        "error": None,
    }

    try:
        # Get appropriate document loader
        loader = get_loader_for_file(file_path)

        # Load the document
        raw_documents = loader.load()

        # Use text splitter for chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", ". ", " ", ""]
        )

        # Create chunks
        documents = text_splitter.split_documents(raw_documents)

        # Update stats
        stats["success"] = True
        stats["chunk_count"] = len(documents)
        stats["original_document_count"] = len(raw_documents)

        logger.info(
            f"Processed {file_path} into {len(documents)} chunks from {len(raw_documents)} original documents"
        )
        return documents, stats

    except Exception as e:
        logger.error(f"Error processing document {file_path}: {e}")
        stats["error"] = str(e)
        return [], stats


def get_vectorstore(docs_dir: str = DOCS_DIR):
    """Get or create a vectorstore from all documents in the docs directory."""
    try:
        # If FAISS index exists, load it
        index_file = os.path.join(docs_dir, "faiss_index")
        if os.path.exists(index_file):
            embeddings = OpenAIEmbeddings()
            vectorstore = FAISS.load_local(index_file, embeddings)
            logger.info(f"Loaded existing vectorstore from {index_file}")
            return vectorstore
    except Exception as e:
        logger.error(f"Error loading existing vectorstore: {e}")

    # Create new vectorstore
    try:
        # Process all documents in the docs directory
        documents = []
        for filename in os.listdir(docs_dir):
            file_path = os.path.join(docs_dir, filename)
            if os.path.isfile(file_path) and not filename.startswith("faiss_index"):
                doc_chunks, _ = process_document(file_path)
                documents.extend(doc_chunks)

        if not documents:
            logger.warning("No documents found to create vectorstore")
            return None

        # Create vectorstore
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(documents, embeddings)

        # Save the vectorstore
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        vectorstore.save_local(index_file)
        logger.info(f"Created new vectorstore with {len(documents)} documents")

        return vectorstore
    except Exception as e:
        logger.error(f"Error creating vectorstore: {e}")
        return None


def query_knowledge_base(query: str, k: int = 3) -> List[Document]:
    """Query the knowledge base for relevant documents."""
    try:
        vectorstore = get_vectorstore()
        if not vectorstore:
            logger.warning("No vectorstore available for querying")
            return []

        results = vectorstore.similarity_search(query, k=k)
        return results
    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}")
        return []


def add_document_to_knowledge_base(
    file_path: str, metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a document and add it to the knowledge base.

    Args:
        file_path: Path to the document file
        metadata: Additional metadata to store with the document

    Returns:
        Dictionary with processing results and status information
    """
    doc_id = os.path.basename(file_path)
    result = {
        "success": False,
        "document_id": doc_id,
        "file_path": file_path,
        "vectorstore_added": False,
        "metadata_added": False,
        "error": None,
    }

    try:
        # Process the document
        documents, processing_stats = process_document(file_path)
        result.update(processing_stats)

        if not documents:
            result["error"] = "No chunks extracted from document"
            return result

        # Add metadata to each document chunk
        user_metadata = metadata or {}
        for doc in documents:
            # Start with document's existing metadata or empty dict
            doc_metadata = doc.metadata or {}
            # Add the user-provided metadata
            doc_metadata.update(user_metadata)
            # Add system metadata
            doc_metadata.update(
                {
                    "document_id": doc_id,
                    "source_file": os.path.basename(file_path),
                    "ingestion_timestamp": datetime.now().isoformat(),
                }
            )
            # Set the updated metadata
            doc.metadata = doc_metadata

        # Get existing vectorstore or create new one
        vectorstore = get_vectorstore()
        if not vectorstore:
            # Create new vectorstore with just this document
            embeddings = OpenAIEmbeddings()
            vectorstore = FAISS.from_documents(documents, embeddings)
        else:
            # Add documents to existing vectorstore
            vectorstore.add_documents(documents)

        # Save updated vectorstore
        index_file = os.path.join(DOCS_DIR, "faiss_index")
        vectorstore.save_local(index_file)

        # Update result
        result["success"] = True
        result["vectorstore_added"] = True

        # Store document metadata
        DOCUMENT_METADATA[doc_id] = {
            "file_path": file_path,
            "user_metadata": user_metadata,
            "processing_stats": processing_stats,
            "ingestion_timestamp": datetime.now().isoformat(),
            "chunk_count": len(documents),
        }
        result["metadata_added"] = True

        logger.info(f"Added {len(documents)} chunks from {file_path} to knowledge base")
        return result

    except Exception as e:
        logger.error(f"Error adding document to knowledge base: {e}")
        result["error"] = str(e)
        return result


def get_document_metadata(doc_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve metadata for a specific document."""
    return DOCUMENT_METADATA.get(doc_id)


def list_all_documents() -> List[Dict[str, Any]]:
    """List all documents with their metadata."""
    return [
        {"document_id": doc_id, **metadata}
        for doc_id, metadata in DOCUMENT_METADATA.items()
    ]
