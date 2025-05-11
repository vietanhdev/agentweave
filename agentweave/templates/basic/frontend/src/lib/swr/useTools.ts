import { useApi } from "../api";
import { Tool } from "./types";
import { useSWRConfig } from "swr";
import { toast } from "@/components/ui/use-toast";

/**
 * Hook for fetching tools
 */
export function useTools() {
  return useApi<{ tools: Tool[] }>("/api/tools/");
}

/**
 * Hook for toggling a tool's enabled status
 */
export function useToggleTool() {
  const { mutate } = useSWRConfig();

  const toggleTool = async (toolName: string, enabled: boolean) => {
    try {
      const response = await fetch(`/api/tools/${toolName}/toggle`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ enabled }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorDetail =
          errorData.error || errorData.detail || "Unknown error";

        // Show a toast notification with the error
        toast({
          title: "Error toggling tool",
          description: `Failed to ${
            enabled ? "enable" : "disable"
          } ${toolName}: ${errorDetail}`,
          variant: "destructive",
        });

        throw new Error(`Failed to toggle tool: ${errorDetail}`);
      }

      // Revalidate the tools cache
      await mutate("/api/tools/");

      // Show success notification
      toast({
        title: "Success",
        description: `Tool ${toolName} ${
          enabled ? "enabled" : "disabled"
        } successfully`,
      });

      return await response.json();
    } catch (error) {
      console.error("Error toggling tool:", error);
      throw error;
    }
  };

  return { toggleTool };
}
