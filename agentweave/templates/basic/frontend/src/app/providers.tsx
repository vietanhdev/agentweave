"use client";

import { ReactNode } from "react";
import { SWRConfig } from "swr";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/toaster";

// Custom fetcher for SWR that handles errors
const fetcher = async (url: string) => {
  const res = await fetch(url);

  // If the status code is not 2xx, throw an error
  if (!res.ok) {
    const error = new Error("An error occurred while fetching the data.");
    // Add extra info to the error object
    throw Object.assign(error, {
      info: await res.json(),
      status: res.status,
    });
  }

  return res.json();
};

export function Providers({ children }: { children: ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher,
        revalidateOnFocus: false,
        shouldRetryOnError: false,
      }}
    >
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        {children}
        <Toaster />
      </ThemeProvider>
    </SWRConfig>
  );
}
