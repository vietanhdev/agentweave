import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useDocumentContent } from "@/lib/api";

interface DocumentViewerProps {
  documentId: string;
  documentName: string;
  isOpen: boolean;
  onClose: () => void;
}

export function DocumentViewer({
  documentId,
  documentName,
  isOpen,
  onClose,
}: DocumentViewerProps) {
  const { getDocumentContent, isLoading, error } = useDocumentContent();
  const [content, setContent] = useState<string | null>(null);
  const [contentType, setContentType] = useState<string | null>(null);
  const [encoding, setEncoding] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && documentId) {
      const fetchContent = async () => {
        try {
          const data = await getDocumentContent(documentId);
          setContent(data.content);
          setContentType(data.content_type);
          setEncoding(data.encoding || null);
        } catch (err) {
          console.error("Error fetching document content:", err);
        }
      };

      fetchContent();
    }
  }, [isOpen, documentId, getDocumentContent]);

  // Reset state when closing
  useEffect(() => {
    if (!isOpen) {
      setContent(null);
      setContentType(null);
      setEncoding(null);
    }
  }, [isOpen]);

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-64">
          Loading document content...
        </div>
      );
    }

    if (error) {
      return (
        <div className="text-red-500 p-4">
          Error loading document: {error.message}
        </div>
      );
    }

    if (!content) {
      return (
        <div className="text-muted-foreground p-4">No content available</div>
      );
    }

    // Handle different content types
    if (contentType) {
      // Plain text
      if (contentType.startsWith("text/plain")) {
        return (
          <pre className="whitespace-pre-wrap p-4 max-h-[70vh] overflow-auto bg-muted/50 rounded-md">
            {content}
          </pre>
        );
      }

      // HTML
      if (contentType.startsWith("text/html")) {
        return (
          <div
            className="max-h-[70vh] overflow-auto p-4 bg-white rounded-md"
            dangerouslySetInnerHTML={{ __html: content }}
          />
        );
      }

      // JSON
      if (contentType.includes("json")) {
        try {
          const formattedJson = JSON.stringify(JSON.parse(content), null, 2);
          return (
            <pre className="whitespace-pre-wrap p-4 max-h-[70vh] overflow-auto bg-muted/50 rounded-md">
              {formattedJson}
            </pre>
          );
        } catch {
          return (
            <pre className="whitespace-pre-wrap p-4 max-h-[70vh] overflow-auto bg-muted/50 rounded-md">
              {content}
            </pre>
          );
        }
      }

      // CSV
      if (contentType.includes("csv")) {
        return (
          <pre className="whitespace-pre-wrap p-4 max-h-[70vh] overflow-auto bg-muted/50 rounded-md">
            {content}
          </pre>
        );
      }

      // Markdown
      if (contentType.includes("markdown")) {
        return (
          <pre className="whitespace-pre-wrap p-4 max-h-[70vh] overflow-auto bg-muted/50 rounded-md">
            {content}
          </pre>
        );
      }

      // PDF (base64 encoded)
      if (contentType === "application/pdf" && encoding === "base64") {
        return (
          <div className="w-full h-[70vh]">
            <iframe
              src={`data:application/pdf;base64,${content}`}
              className="w-full h-full rounded-md border"
              title={documentName}
            />
          </div>
        );
      }

      // Images (base64 encoded)
      if (contentType.startsWith("image/") && encoding === "base64") {
        return (
          <div className="flex justify-center max-h-[70vh] overflow-auto">
            <img
              src={`data:${contentType};base64,${content}`}
              alt={documentName}
              className="max-w-full max-h-full rounded-md"
            />
          </div>
        );
      }
    }

    // Fallback for other content types
    return (
      <div className="text-muted-foreground p-4">
        This document type cannot be previewed.
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl w-full">
        <DialogHeader>
          <DialogTitle>{documentName}</DialogTitle>
        </DialogHeader>
        <div className="mt-4">{renderContent()}</div>
      </DialogContent>
    </Dialog>
  );
}
