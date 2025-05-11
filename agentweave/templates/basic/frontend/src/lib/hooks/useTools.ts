import { useRequest } from "./useRequest";
import { Tool } from "./types";

/**
 * Hook for fetching tools
 */
export function useTools() {
  return useRequest<{ tools: Tool[] }>("/api/tools/");
}
