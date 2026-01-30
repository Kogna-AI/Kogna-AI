/**
 * Custom render function with common providers.
 *
 * This file provides a custom render function that wraps components
 * with all necessary providers (QueryClient, theme, auth, etc.)
 * for consistent test setup.
 */

import React, { ReactElement, ReactNode } from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

/**
 * Options for custom render function.
 */
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  /**
   * Initial route for the test.
   */
  initialRoute?: string

  /**
   * Custom QueryClient instance.
   * If not provided, a new client with test defaults is created.
   */
  queryClient?: QueryClient

  /**
   * Initial auth state for testing authenticated components.
   */
  authState?: {
    isAuthenticated: boolean
    user?: {
      id: string
      email: string
      first_name: string
      second_name: string
      organization_id?: string
    } | null
    accessToken?: string | null
  }
}

/**
 * Create a QueryClient with test-friendly defaults.
 * Disables retries and caching for predictable test behavior.
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

/**
 * Default wrapper for tests.
 * Includes QueryClientProvider and other common providers.
 */
interface WrapperProps {
  children: ReactNode
  queryClient?: QueryClient
}

function createWrapper(options: CustomRenderOptions = {}) {
  const queryClient = options.queryClient ?? createTestQueryClient()

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

/**
 * Custom render function that wraps components with providers.
 *
 * @example
 * ```tsx
 * import { customRender, screen } from '@/test-utils'
 *
 * test('renders component', () => {
 *   customRender(<MyComponent />)
 *   expect(screen.getByText('Hello')).toBeInTheDocument()
 * })
 * ```
 */
export function customRender(
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult & { queryClient: QueryClient } {
  const queryClient = options.queryClient ?? createTestQueryClient()
  const Wrapper = createWrapper({ ...options, queryClient })

  const result = render(ui, { wrapper: Wrapper, ...options })

  return {
    ...result,
    queryClient,
  }
}

/**
 * Render hook wrapper for testing custom hooks.
 *
 * @example
 * ```tsx
 * import { renderHook } from '@testing-library/react'
 * import { createHookWrapper } from '@/test-utils'
 *
 * test('custom hook', () => {
 *   const { result } = renderHook(() => useMyHook(), {
 *     wrapper: createHookWrapper(),
 *   })
 * })
 * ```
 */
export function createHookWrapper(options: CustomRenderOptions = {}) {
  return createWrapper(options)
}

/**
 * Wait for queries to settle.
 * Useful when testing components that fetch data on mount.
 */
export async function waitForQueries(queryClient: QueryClient): Promise<void> {
  await queryClient.cancelQueries()
  await new Promise((resolve) => setTimeout(resolve, 0))
}
