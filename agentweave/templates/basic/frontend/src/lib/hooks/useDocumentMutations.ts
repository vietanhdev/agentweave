import { useMutation } from "./useMutation";
import { Document } from "./types";

/**
 * Hook for uploading documents
 */
export function useUploadDocument() {
  interface UploadMetadata {
    description?: string;
    tags?: string[];
    category?: string;
  }

  interface UploadResponse {
    status: string;
    document: Document;
  }

  const uploadFn = async ({
    file,
    metadata,
  }: {
    file: File;
    metadata: UploadMetadata;
  }): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    // Add metadata
    if (metadata.description) {
      formData.append("description", metadata.description);
    }

    if (metadata.tags && metadata.tags.length > 0) {
      formData.append("tags", metadata.tags.join(","));
    }

    if (metadata.category) {
      formData.append("category", metadata.category);
    }

    const response = await fetch("/api/documents/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw Object.assign(new Error("Failed to upload document"), {
        info: errorData,
        status: response.status,
      });
    }

    return response.json();
  };

  return useMutation(uploadFn);
}

/**
 * Hook for deleting documents
 */
export function useDeleteDocument() {
  interface DeleteResponse {
    status: string;
    message: string;
  }

  const deleteFn = async (documentId: string): Promise<DeleteResponse> => {
    const response = await fetch(`/api/documents/${documentId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw Object.assign(new Error("Failed to delete document"), {
        info: errorData,
        status: response.status,
      });
    }

    return response.json();
  };

  return useMutation(deleteFn);
}

/**
 * Hook for reprocessing documents
 */
export function useReprocessDocument() {
  interface ReprocessResponse {
    status: string;
    document_id: string;
    ingestion_status: {
      processed: boolean;
      chunk_count: number;
      error?: string;
    };
  }

  const reprocessFn = async (
    documentId: string,
  ): Promise<ReprocessResponse> => {
    const response = await fetch(`/api/documents/${documentId}/reprocess`, {
      method: "POST",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw Object.assign(new Error("Failed to reprocess document"), {
        info: errorData,
        status: response.status,
      });
    }

    return response.json();
  };

  return useMutation(reprocessFn);
}
