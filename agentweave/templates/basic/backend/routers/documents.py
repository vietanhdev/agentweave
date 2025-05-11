"""
Router for document-related endpoints.
"""

import logging
import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Query
from pydantic import BaseModel

from agents.document_processor import (
    add_document_to_knowledge_base,
    get_document_metadata,
    list_all_documents,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Temporary storage for uploaded documents
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documents")
os.makedirs(DOCS_DIR, exist_ok=True)


class DocumentMetadata(BaseModel):
    """Model for document metadata."""

    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class Document(BaseModel):
    """Model for document metadata."""

    id: str
    filename: str
    size: int
    type: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    ingestion_status: Optional[Dict[str, Any]] = None
    chunk_count: Optional[int] = None
    created_at: Optional[str] = None


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
):
    """Upload a document to use as knowledge base."""
    try:
        # Create a unique ID for the file
        doc_id = f"{os.urandom(4).hex()}_{file.filename}"
        file_path = os.path.join(DOCS_DIR, doc_id)

        # Save the file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            file_size = len(content)

        # Prepare metadata
        metadata = {
            "description": description,
            "tags": tags.split(",") if tags else [],
            "category": category,
            "filename": file.filename,
            "content_type": file.content_type,
        }

        # Process the document and add to knowledge base
        ingestion_result = add_document_to_knowledge_base(file_path, metadata)

        # Check if processing succeeded
        if not ingestion_result["success"]:
            logger.warning(
                f"Document {doc_id} was saved but could not be processed: {ingestion_result.get('error', 'Unknown error')}"
            )

        return {
            "status": "success",
            "document": {
                "id": doc_id,
                "filename": file.filename,
                "size": file_size,
                "type": file.content_type or "application/octet-stream",
                "description": description,
                "tags": metadata["tags"],
                "category": category,
                "ingestion_status": {
                    "processed": ingestion_result["success"],
                    "chunk_count": ingestion_result.get("chunk_count", 0),
                    "error": ingestion_result.get("error"),
                },
            },
        }
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_documents(
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
):
    """List all uploaded documents with optional filtering."""
    try:
        # Try to get documents from document processor metadata
        processor_docs = list_all_documents()

        if processor_docs:
            # Use the metadata from the document processor
            documents = []

            for doc_meta in processor_docs:
                # Skip if we're filtering by category and it doesn't match
                if (
                    category
                    and doc_meta.get("user_metadata", {}).get("category") != category
                ):
                    continue

                # Skip if we're filtering by tag and it doesn't match
                if tag and tag not in doc_meta.get("user_metadata", {}).get("tags", []):
                    continue

                # Extract document details
                doc_id = doc_meta["document_id"]
                user_metadata = doc_meta.get("user_metadata", {})
                processing_stats = doc_meta.get("processing_stats", {})

                documents.append(
                    {
                        "id": doc_id,
                        "filename": user_metadata.get("filename", doc_id),
                        "size": processing_stats.get("file_size", 0),
                        "type": user_metadata.get(
                            "content_type", "application/octet-stream"
                        ),
                        "description": user_metadata.get("description"),
                        "tags": user_metadata.get("tags", []),
                        "category": user_metadata.get("category"),
                        "chunk_count": doc_meta.get("chunk_count", 0),
                        "created_at": doc_meta.get("ingestion_timestamp"),
                    }
                )

            return {"documents": documents}

        # Fallback to file system if no processor metadata
        documents = []
        for filename in os.listdir(DOCS_DIR):
            file_path = os.path.join(DOCS_DIR, filename)
            # Skip directories and special files like the faiss_index
            if os.path.isfile(file_path) and not filename.startswith("faiss_index"):
                # Extract original filename from the stored name
                original_filename = "_".join(filename.split("_")[1:])
                documents.append(
                    {
                        "id": filename,
                        "filename": original_filename,
                        "size": os.path.getsize(file_path),
                        "type": "application/octet-stream",  # We don't store this info currently
                    }
                )

        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """Get details for a specific document."""
    try:
        # Try to get from document processor metadata
        doc_meta = get_document_metadata(doc_id)

        if doc_meta:
            user_metadata = doc_meta.get("user_metadata", {})
            processing_stats = doc_meta.get("processing_stats", {})

            return {
                "document": {
                    "id": doc_id,
                    "filename": user_metadata.get("filename", doc_id),
                    "size": processing_stats.get("file_size", 0),
                    "type": user_metadata.get(
                        "content_type", "application/octet-stream"
                    ),
                    "description": user_metadata.get("description"),
                    "tags": user_metadata.get("tags", []),
                    "category": user_metadata.get("category"),
                    "chunk_count": doc_meta.get("chunk_count", 0),
                    "created_at": doc_meta.get("ingestion_timestamp"),
                    "ingestion_status": {
                        "processed": processing_stats.get("success", False),
                        "chunk_count": processing_stats.get("chunk_count", 0),
                        "error": processing_stats.get("error"),
                    },
                }
            }

        # Fallback to file system check
        file_path = os.path.join(DOCS_DIR, doc_id)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        # Extract original filename from the stored name
        original_filename = "_".join(doc_id.split("_")[1:])

        return {
            "document": {
                "id": doc_id,
                "filename": original_filename,
                "size": os.path.getsize(file_path),
                "type": "application/octet-stream",
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from both storage and knowledge base."""
    try:
        file_path = os.path.join(DOCS_DIR, doc_id)

        # Check if file exists
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete the file
        os.remove(file_path)

        # TODO: Remove the document from the knowledge base
        # This would be implemented in your document processor

        return {
            "status": "success",
            "message": f"Document {doc_id} deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}/content")
async def get_document_content(doc_id: str):
    """Get the content of a document for viewing in the browser."""
    try:
        file_path = os.path.join(DOCS_DIR, doc_id)

        # Check if file exists
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="Document not found")

        # Get document metadata to determine content type
        doc_meta = get_document_metadata(doc_id)
        content_type = "application/octet-stream"  # Default content type

        if doc_meta and doc_meta.get("user_metadata", {}).get("content_type"):
            content_type = doc_meta["user_metadata"]["content_type"]

        # For text-based files, return the content directly
        text_content_types = [
            "text/plain",
            "text/html",
            "text/csv",
            "application/json",
            "text/markdown",
            "application/xml",
            "text/xml",
        ]

        if any(content_type.startswith(prefix) for prefix in text_content_types):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"content": content, "content_type": content_type}

        # For binary files like PDFs, images, etc., return base64 encoded content
        import base64

        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        return {"content": content, "content_type": content_type, "encoding": "base64"}

    except HTTPException:
        raise
    except UnicodeDecodeError:
        # If we can't decode as UTF-8, it's likely a binary file
        import base64

        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        return {"content": content, "content_type": content_type, "encoding": "base64"}
    except Exception as e:
        logger.error(f"Error retrieving document content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{doc_id}/reprocess")
async def reprocess_document(doc_id: str):
    """Reprocess a document to update the knowledge base."""
    try:
        file_path = os.path.join(DOCS_DIR, doc_id)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        # Get current metadata if available
        doc_meta = get_document_metadata(doc_id)
        user_metadata = doc_meta.get("user_metadata", {}) if doc_meta else {}

        # Reprocess the document
        ingestion_result = add_document_to_knowledge_base(file_path, user_metadata)

        return {
            "status": "success",
            "document_id": doc_id,
            "ingestion_status": {
                "processed": ingestion_result["success"],
                "chunk_count": ingestion_result.get("chunk_count", 0),
                "error": ingestion_result.get("error"),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reprocessing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
