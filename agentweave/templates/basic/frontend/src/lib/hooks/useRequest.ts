import useSWR, { SWRConfiguration, SWRResponse } from "swr";
import { fetcher, ApiError } from "./fetcher";

/**
 * Generic hook for GET requests
 */
export function useRequest<T>(
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
