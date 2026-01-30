/**
 * Test utilities barrel export.
 *
 * This module re-exports all test utilities for easy importing.
 *
 * @example
 * ```tsx
 * import {
 *   customRender,
 *   createMockUser,
 *   createMockKPI,
 *   screen,
 *   userEvent,
 * } from '@/test-utils'
 * ```
 */

// Re-export testing library utilities
export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'

// Export custom render function and helpers
export {
  customRender,
  createTestQueryClient,
  createHookWrapper,
  waitForQueries,
} from './render'

// Export mock data generators
export {
  // ID utilities
  generateId,
  resetIdCounter,
  // User data
  createMockUser,
  createMockAdminUser,
  // Team data
  createMockTeam,
  createMockTeams,
  // KPI data
  createMockKPI,
  createMockKPIs,
  // Objective data
  createMockObjective,
  createMockObjectives,
  // Insight data
  createMockInsight,
  createMockInsights,
  // Connector data
  createMockConnector,
  // Conversation data
  createMockConversation,
  createMockMessage,
  // API response helpers
  createMockKPIDashboardResponse,
  // Auth helpers
  createMockAuthState,
  createMockUnauthenticatedState,
  // Error response helpers
  createMockValidationError,
  createMockUnauthorizedError,
  createMockForbiddenError,
  createMockNotFoundError,
  createMockServerError,
} from './mockData'

// Export types
export type {
  MockUser,
  MockTeam,
  MockKPI,
  MockObjective,
  MockInsight,
  MockConnector,
  MockConversation,
  MockMessage,
  MockKPIDashboardResponse,
  MockAuthState,
  MockErrorResponse,
} from './mockData'

// Re-export MSW utilities for test-specific overrides
export { http, HttpResponse } from 'msw'
export { server } from '../mocks/server'
