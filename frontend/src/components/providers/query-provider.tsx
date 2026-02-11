'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useState } from 'react'

/**
 * TanStack Query provider with smart defaults for Smart Shamba.
 *
 * Caching strategy:
 *  - staleTime: 2 min  → data is "fresh" for 2 min (no refetch on mount)
 *  - gcTime:    10 min → unused cache entries are garbage collected after 10 min
 *  - refetchOnWindowFocus: true → background refetch when user returns to tab
 *  - retry: 2 → retry failed requests twice before showing error
 *
 * Works in tandem with Redis backend cache:
 *  - TanStack Query prevents redundant network requests per user
 *  - Redis prevents redundant DB/API calls across all users
 */
export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 2 * 60 * 1000,      // 2 minutes
            gcTime: 10 * 60 * 1000,         // 10 minutes
            refetchOnWindowFocus: true,
            refetchOnReconnect: true,
            retry: 2,
            retryDelay: (attempt: number) => Math.min(1000 * 2 ** attempt, 10000),
          },
          mutations: {
            retry: 1,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />
      )}
    </QueryClientProvider>
  )
}
