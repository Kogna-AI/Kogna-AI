/**
 * MSW server for Node.js environment (used in tests).
 *
 * This sets up the mock server for Vitest tests.
 */

import { setupServer } from 'msw/node'
import { handlers } from './handlers'

// Create the mock server with default handlers
export const server = setupServer(...handlers)
