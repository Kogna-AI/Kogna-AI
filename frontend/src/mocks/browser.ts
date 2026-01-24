/**
 * MSW browser worker for development environment.
 *
 * This can be used to mock API responses during development.
 * To enable, import and call setupMocks() in your app entry point.
 */

import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

// Create the browser worker with default handlers
export const worker = setupWorker(...handlers)

/**
 * Initialize MSW in development mode.
 * Call this function in your app entry point (e.g., App.tsx) during development.
 *
 * Example:
 * ```ts
 * if (process.env.NODE_ENV === 'development') {
 *   setupMocks()
 * }
 * ```
 */
export async function setupMocks() {
  if (typeof window !== 'undefined') {
    return worker.start({
      onUnhandledRequest: 'bypass', // Don't warn about unhandled requests
    })
  }
}
