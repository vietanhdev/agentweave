/**
 * Base fetcher for SWR hooks
 */

// Define the base fetcher function
export const fetcher = async <T>(url: string): Promise<T> => {
  const response = await fetch(url);

  // If the status code is not 2xx, throw an error
  if (!response.ok) {
    const error = new Error("An error occurred while fetching the data.");
    // Add extra info to the error object
    throw Object.assign(error, {
      info: await response.json().catch(() => ({})),
      status: response.status,
    });
  }

  return response.json();
};

// Type for API error
export interface ApiError {
  info?: any;
  status?: number;
  message: string;
}
