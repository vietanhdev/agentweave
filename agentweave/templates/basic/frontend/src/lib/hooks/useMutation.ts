import { useState } from "react";
import { toast } from "@/components/ui/use-toast";
import { ApiError } from "./fetcher";

interface MutationOptions<TData, TVariables> {
  /**
   * Function to run before the mutation
   */
  onMutate?: (variables: TVariables) => void;

  /**
   * Function to run on success
   */
  onSuccess?: (data: TData, variables: TVariables) => void;

  /**
   * Function to run on error
   */
  onError?: (error: ApiError, variables: TVariables) => void;

  /**
   * Function to run after the mutation (success or error)
   */
  onSettled?: (data?: TData, error?: ApiError, variables?: TVariables) => void;

  /**
   * Whether to show toast notifications on error
   */
  showErrorToast?: boolean;
}

/**
 * Hook for handling mutation operations (POST, PUT, DELETE)
 */
export function useMutation<TData = unknown, TVariables = unknown>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options: MutationOptions<TData, TVariables> = {},
) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [data, setData] = useState<TData | null>(null);

  const {
    onMutate,
    onSuccess,
    onError,
    onSettled,
    showErrorToast = true,
  } = options;

  const mutate = async (variables: TVariables): Promise<TData> => {
    setIsLoading(true);
    setError(null);

    try {
      // Run onMutate if provided
      if (onMutate) {
        onMutate(variables);
      }

      // Execute the mutation
      const result = await mutationFn(variables);

      // Update state and run callbacks
      setData(result);
      if (onSuccess) {
        onSuccess(result, variables);
      }

      // Run onSettled
      if (onSettled) {
        onSettled(result, undefined, variables);
      }

      return result;
    } catch (err: any) {
      // Format the error
      const apiError: ApiError = {
        message: err.message || "An error occurred",
        info: err.info,
        status: err.status,
      };

      // Update state
      setError(apiError);

      // Run callbacks
      if (onError) {
        onError(apiError, variables);
      }

      if (onSettled) {
        onSettled(undefined, apiError, variables);
      }

      // Show toast notification
      if (showErrorToast) {
        toast({
          title: "Error",
          description: apiError.message,
          variant: "destructive",
        });
      }

      throw apiError;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    mutate,
    isLoading,
    error,
    data,
  };
}
