'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect } from 'react';

// Simple cache persistence using sessionStorage
function getCachedQueries() {
  if (typeof window === 'undefined') return null;
  try {
    const cached = sessionStorage.getItem('react-query-cache');
    return cached ? JSON.parse(cached) : null;
  } catch {
    return null;
  }
}

function setCachedQueries(data: any) {
  if (typeof window === 'undefined') return;
  try {
    sessionStorage.setItem('react-query-cache', JSON.stringify(data));
  } catch {
    // Ignore storage errors
  }
}

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Increased staleTime for better caching across refreshes
            staleTime: 5 * 60 * 1000, // 5 minutes - data considered fresh
            gcTime: 10 * 60 * 1000, // 10 minutes - keep in cache (formerly cacheTime)
            refetchOnWindowFocus: false, // Don't refetch on window focus
            refetchOnMount: false, // Don't refetch on component mount if data is fresh
            retry: 1, // Retry failed requests once
          },
        },
      })
  );

  // Restore cache from sessionStorage on mount
  useEffect(() => {
    const cached = getCachedQueries();
    if (cached?.queries) {
      // Restore queries to cache
      cached.queries.forEach((query: any) => {
        if (query.state?.data && query.queryKey) {
          queryClient.setQueryData(query.queryKey, query.state.data, {
            updatedAt: query.state.dataUpdatedAt,
          });
        }
      });
    }
  }, [queryClient]);

  // Save cache to sessionStorage periodically and on navigation
  useEffect(() => {
    const saveCache = () => {
      const cache = queryClient.getQueryCache();
      const queries = cache.getAll().map((query) => ({
        queryKey: query.queryKey,
        state: {
          data: query.state.data,
          dataUpdatedAt: query.state.dataUpdatedAt,
        },
      }));
      setCachedQueries({ queries });
    };

    // Save periodically
    const interval = setInterval(saveCache, 1000);

    // Save immediately before page unload/refresh
    window.addEventListener('beforeunload', saveCache);

    return () => {
      clearInterval(interval);
      window.removeEventListener('beforeunload', saveCache);
      saveCache(); // Save one last time on unmount
    };
  }, [queryClient]);

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}