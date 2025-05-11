import { useRequest } from "./useRequest";
import { Document } from "./types";

/**
 * Hook for fetching documents
 *
 * @param category Optional category filter
 * @param tag Optional tag filter
 */
export function useDocuments(category?: string, tag?: string) {
  // Build query parameters if any are provided
  let url = "/api/documents/";
  const params = new URLSearchParams();

  if (category) params.append("category", category);
  if (tag) params.append("tag", tag);

  const queryString = params.toString();
  if (queryString) url += `?${queryString}`;

  return useRequest<{ documents: Document[] }>(url);
}
