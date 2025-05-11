/**
 * Common types for API requests and responses
 */

// Document types
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

// Query types
export interface QueryRequest {
  query: string;
  conversation_id?: string | null;
  context?: Record<string, any>;
}

export interface QueryResponse {
  response: string;
  conversation_id: string;
  metadata?: {
    execution_steps?: any[];
    [key: string]: any;
  };
}

// Tool types
export interface Tool {
  name: string;
  description: string;
  parameters: any;
  required_parameters: string[];
  enabled: boolean;
}
