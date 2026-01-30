/**
 * Vitest test setup file.
 *
 * This file runs before all tests and sets up:
 * - Testing library matchers (@testing-library/jest-dom)
 * - MSW (Mock Service Worker) server for API mocking
 * - Common global mocks (Next.js router, Image, window APIs)
 */

import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, afterAll, vi } from 'vitest'
import { server } from './src/mocks/server'

// ==================== MSW SERVER SETUP ====================

/**
 * Start MSW server before all tests.
 * The onUnhandledRequest option determines how to handle requests
 * that don't match any handler.
 */
beforeAll(() => {
  server.listen({
    onUnhandledRequest: 'warn', // Log warnings for unhandled requests
  })
})

/**
 * Reset handlers after each test to ensure test isolation.
 * This removes any runtime handlers added during tests.
 */
afterEach(() => {
  cleanup()
  server.resetHandlers()
})

/**
 * Close MSW server after all tests complete.
 */
afterAll(() => {
  server.close()
})

// ==================== NEXT.JS MOCKS ====================

/**
 * Mock Next.js navigation hooks.
 */
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
  redirect: vi.fn(),
  notFound: vi.fn(),
}))

/**
 * Mock Next.js Image component.
 * Returns a simple img element for testing purposes.
 */
vi.mock('next/image', () => ({
  default: (props: Record<string, unknown>) => {
    return {
      $$typeof: Symbol.for('react.element'),
      type: 'img',
      props: {
        src: props.src,
        alt: props.alt,
        width: props.width,
        height: props.height,
        ...props,
      },
      key: null,
      ref: null,
    }
  },
}))

/**
 * Mock Next.js Link component.
 */
vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) => {
    return {
      $$typeof: Symbol.for('react.element'),
      type: 'a',
      props: { href, ...props, children },
      key: null,
      ref: null,
    }
  },
}))

// ==================== BROWSER API MOCKS ====================

/**
 * Mock window.matchMedia for responsive design tests.
 */
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

/**
 * Mock ResizeObserver for components that observe size changes.
 */
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

/**
 * Mock IntersectionObserver for lazy loading and visibility detection.
 */
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  root: null,
  rootMargin: '',
  thresholds: [],
  takeRecords: vi.fn(),
}))

/**
 * Mock scrollTo for scroll behavior tests.
 */
window.scrollTo = vi.fn()

/**
 * Mock localStorage for storage tests.
 */
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

/**
 * Mock sessionStorage for storage tests.
 */
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
}
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
})

// ==================== CONSOLE SETUP ====================

/**
 * Suppress specific console warnings during tests.
 * Add patterns here for known warnings that are safe to ignore.
 */
const originalConsoleError = console.error
console.error = (...args: unknown[]) => {
  // Suppress React act() warnings that sometimes occur in tests
  if (typeof args[0] === 'string' && args[0].includes('Warning: An update to')) {
    return
  }
  originalConsoleError.apply(console, args)
}
