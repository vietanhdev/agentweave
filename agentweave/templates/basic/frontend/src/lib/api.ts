import useSWR, { SWRConfiguration, SWRResponse } from "swr";
import { useState } from "react";
import { toast } from "@/components/ui/use-toast";

// Define the base fetcher function
const fetcher = async <T>(url: string): Promise<T> => {
  const response = await fetch(url);

  // If the status code is not 2xx, throw an error
  if (!response.ok) {
    const error = new Error("An error occurred while fetching the data.");
    // Add extra info to the error object
    throw Object.assign(error, {
      info: await response.json(),
      status: response.status,
    });
  }

  return response.json();
};

// Type for API error
interface ApiError {
  info?: any;
  status?: number;
  message: string;
}

// Generic hook for GET requests
export function useApi<T>(
  url: string,
  config?: SWRConfiguration,
): SWRResponse<T, ApiError> & { isLoading: boolean } {
  const { data, error, mutate, isValidating, ...rest } = useSWR<T, ApiError>(
    url,
    fetcher,
    config,
  );

  return {
    data,
    error,
    mutate,
    isValidating,
    // Loading state when we have no data and no error, or when revalidating
    isLoading: (!error && !data) || isValidating,
    ...rest,
  };
}

// Hook for fetching documents
export function useDocuments() {
  return useApi<{ documents: any[] }>("/api/documents/");
}

// Type for query response
interface QueryResponse {
  response: string;
  conversation_id: string;
  metadata?: {
    execution_steps?: any[];
    [key: string]: any;
  };
}

// Type for query request
interface QueryRequest {
  query: string;
  conversation_id?: string | null;
  context?: Record<string, any>;
}

// Hook for sending queries
export function useSendQuery() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const sendQuery = async (request: QueryRequest): Promise<QueryResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw Object.assign(new Error("Failed to send query"), {
          info: errorData,
          status: response.status,
        });
      }

      return await response.json();
    } catch (err: any) {
      const apiError: ApiError = {
        message: err.message || "An error occurred",
        info: err.info,
        status: err.status,
      };
      setError(apiError);
      // Show toast notification
      toast({
        title: "Error",
        description: apiError.message,
        variant: "destructive",
      });
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  };

  return { sendQuery, isLoading, error };
}

// Type for document metadata
export interface Document {
  id: string;
  filename: string;
  size: number;
  type: string;
  description?: string;
  tags?: string[];
  category?: string;
  chunk_count?: number;
  created_at?: string;
  ingestion_status?: {
    processed: boolean;
    chunk_count: number;
    error?: string;
  };
}

// Hook for file uploads
export function useUploadDocument() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const uploadDocument = async (
    file: File,
    metadata: {
      description?: string;
      tags?: string[];
      category?: string;
    },
  ): Promise<any> => {
    setIsLoading(true);
    setError(null);

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

    try {
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

      return await response.json();
    } catch (err: any) {
      const apiError: ApiError = {
        message: err.message || "An error occurred",
        info: err.info,
        status: err.status,
      };
      setError(apiError);
      // Show toast notification
      toast({
        title: "Error",
        description: apiError.message,
        variant: "destructive",
      });
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  };

  return { uploadDocument, isLoading, error };
}

// Hook for deleting documents
export function useDeleteDocument() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const deleteDocument = async (documentId: string): Promise<any> => {
    setIsLoading(true);
    setError(null);

    try {
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

      return await response.json();
    } catch (err: any) {
      const apiError: ApiError = {
        message: err.message || "An error occurred",
        info: err.info,
        status: err.status,
      };
      setError(apiError);
      // Show toast notification
      toast({
        title: "Error",
        description: apiError.message,
        variant: "destructive",
      });
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  };

  return { deleteDocument, isLoading, error };
}

// Hook for fetching document content
export function useDocumentContent() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const getDocumentContent = async (documentId: string): Promise<any> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/documents/${documentId}/content`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw Object.assign(new Error("Failed to retrieve document content"), {
          info: errorData,
          status: response.status,
        });
      }

      return await response.json();
    } catch (err: any) {
      const apiError: ApiError = {
        message: err.message || "An error occurred",
        info: err.info,
        status: err.status,
      };
      setError(apiError);
      // Show toast notification
      toast({
        title: "Error",
        description: apiError.message,
        variant: "destructive",
      });
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  };

  return { getDocumentContent, isLoading, error };
}

// Export tool hooks from their correct location
export { useTools } from "./hooks/useTools";
export { useToggleTool } from "./swr/useTools";
