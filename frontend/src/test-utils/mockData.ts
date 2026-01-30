/**
 * Mock data generators for frontend tests.
 *
 * This module provides factory functions to generate realistic test data
 * for various entities used in the Kogna-AI frontend.
 */

// ==================== ID GENERATORS ====================

let idCounter = 0

/**
 * Generate a unique ID for test data.
 */
export function generateId(prefix = 'test'): string {
  idCounter += 1
  return `${prefix}-${idCounter}-${Date.now()}`
}

/**
 * Reset the ID counter (call in beforeEach if needed).
 */
export function resetIdCounter(): void {
  idCounter = 0
}

// ==================== USER DATA ====================

export interface MockUser {
  id: string
  email: string
  first_name: string
  second_name: string
  organization_id: string | null
  role: string
  created_at: string
}

export function createMockUser(overrides: Partial<MockUser> = {}): MockUser {
  const id = generateId('user')
  return {
    id,
    email: `user-${id}@example.com`,
    first_name: 'Test',
    second_name: 'User',
    organization_id: 'org-001',
    role: 'member',
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

export function createMockAdminUser(overrides: Partial<MockUser> = {}): MockUser {
  return createMockUser({
    role: 'admin',
    email: `admin-${generateId('admin')}@example.com`,
    first_name: 'Admin',
    ...overrides,
  })
}

// ==================== TEAM DATA ====================

export interface MockTeam {
  id: string
  name: string
  organization_id: string
  description?: string
  members_count: number
  created_at: string
}

export function createMockTeam(overrides: Partial<MockTeam> = {}): MockTeam {
  const id = generateId('team')
  return {
    id,
    name: `Team ${id}`,
    organization_id: 'org-001',
    description: 'A test team',
    members_count: 5,
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

export function createMockTeams(count: number, overrides: Partial<MockTeam> = {}): MockTeam[] {
  return Array.from({ length: count }, () => createMockTeam(overrides))
}

// ==================== KPI DATA ====================

export interface MockKPI {
  id: string
  name: string
  value: number
  unit: string
  trend: number
  trend_direction: 'up' | 'down' | 'stable'
  organization_id: string
  team_id: string | null
  period: string
  created_at: string
}

export function createMockKPI(overrides: Partial<MockKPI> = {}): MockKPI {
  const id = generateId('kpi')
  const trend = Math.random() * 20 - 10 // Random between -10 and 10
  return {
    id,
    name: `KPI ${id}`,
    value: Math.floor(Math.random() * 10000),
    unit: 'count',
    trend: Math.round(trend * 10) / 10,
    trend_direction: trend > 0 ? 'up' : trend < 0 ? 'down' : 'stable',
    organization_id: 'org-001',
    team_id: null,
    period: new Date().toISOString().slice(0, 7), // YYYY-MM format
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

export function createMockKPIs(count: number, overrides: Partial<MockKPI> = {}): MockKPI[] {
  return Array.from({ length: count }, () => createMockKPI(overrides))
}

// ==================== OBJECTIVE DATA ====================

export interface MockObjective {
  id: string
  name: string
  description: string
  status: 'not_started' | 'in_progress' | 'on_track' | 'at_risk' | 'completed'
  progress: number
  organization_id: string
  team_responsible: string
  due_date: string
  created_at: string
}

export function createMockObjective(overrides: Partial<MockObjective> = {}): MockObjective {
  const id = generateId('obj')
  return {
    id,
    name: `Objective ${id}`,
    description: 'A test objective description',
    status: 'in_progress',
    progress: Math.floor(Math.random() * 100),
    organization_id: 'org-001',
    team_responsible: 'team-001',
    due_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

export function createMockObjectives(count: number, overrides: Partial<MockObjective> = {}): MockObjective[] {
  return Array.from({ length: count }, () => createMockObjective(overrides))
}

// ==================== INSIGHT DATA ====================

export interface MockInsight {
  id: string
  title: string
  content: string
  category: 'revenue' | 'performance' | 'risk' | 'opportunity'
  priority: 'low' | 'medium' | 'high' | 'critical'
  organization_id: string
  source: string
  created_at: string
}

export function createMockInsight(overrides: Partial<MockInsight> = {}): MockInsight {
  const id = generateId('insight')
  const categories: MockInsight['category'][] = ['revenue', 'performance', 'risk', 'opportunity']
  const priorities: MockInsight['priority'][] = ['low', 'medium', 'high', 'critical']

  return {
    id,
    title: `Insight ${id}`,
    content: 'This is a test insight with important information.',
    category: categories[Math.floor(Math.random() * categories.length)],
    priority: priorities[Math.floor(Math.random() * priorities.length)],
    organization_id: 'org-001',
    source: 'ai_analysis',
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

export function createMockInsights(count: number, overrides: Partial<MockInsight> = {}): MockInsight[] {
  return Array.from({ length: count }, () => createMockInsight(overrides))
}

// ==================== CONNECTOR DATA ====================

export interface MockConnector {
  id: string
  type: 'jira' | 'google_drive' | 'microsoft_teams' | 'asana' | 'slack'
  name: string
  status: 'connected' | 'disconnected' | 'error' | 'syncing'
  organization_id: string
  last_sync: string | null
  config: Record<string, unknown>
}

export function createMockConnector(overrides: Partial<MockConnector> = {}): MockConnector {
  const id = generateId('conn')
  return {
    id,
    type: 'jira',
    name: 'Jira Cloud',
    status: 'connected',
    organization_id: 'org-001',
    last_sync: new Date().toISOString(),
    config: {},
    ...overrides,
  }
}

// ==================== CONVERSATION DATA ====================

export interface MockConversation {
  id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
}

export interface MockMessage {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export function createMockConversation(overrides: Partial<MockConversation> = {}): MockConversation {
  const id = generateId('conv')
  const now = new Date().toISOString()
  return {
    id,
    user_id: 'user-001',
    title: `Conversation ${id}`,
    created_at: now,
    updated_at: now,
    ...overrides,
  }
}

export function createMockMessage(overrides: Partial<MockMessage> = {}): MockMessage {
  const id = generateId('msg')
  return {
    id,
    conversation_id: 'conv-001',
    role: 'user',
    content: 'This is a test message.',
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

// ==================== API RESPONSE HELPERS ====================

export interface MockKPIDashboardResponse {
  kpis: MockKPI[]
  summary: {
    total_kpis: number
    positive_trends: number
    negative_trends: number
    period: string
  }
  last_updated: string
}

export function createMockKPIDashboardResponse(kpiCount = 5): MockKPIDashboardResponse {
  const kpis = createMockKPIs(kpiCount)
  return {
    kpis,
    summary: {
      total_kpis: kpis.length,
      positive_trends: kpis.filter((k) => k.trend > 0).length,
      negative_trends: kpis.filter((k) => k.trend < 0).length,
      period: new Date().toISOString().slice(0, 7),
    },
    last_updated: new Date().toISOString(),
  }
}

// ==================== AUTH HELPERS ====================

export interface MockAuthState {
  isAuthenticated: boolean
  user: MockUser | null
  accessToken: string | null
  refreshToken: string | null
}

export function createMockAuthState(overrides: Partial<MockAuthState> = {}): MockAuthState {
  return {
    isAuthenticated: true,
    user: createMockUser(),
    accessToken: 'mock-access-token',
    refreshToken: 'mock-refresh-token',
    ...overrides,
  }
}

export function createMockUnauthenticatedState(): MockAuthState {
  return {
    isAuthenticated: false,
    user: null,
    accessToken: null,
    refreshToken: null,
  }
}

// ==================== ERROR RESPONSE HELPERS ====================

export interface MockErrorResponse {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>
}

export function createMockValidationError(
  field: string,
  message: string
): { status: number; body: MockErrorResponse } {
  return {
    status: 422,
    body: {
      detail: [
        {
          loc: ['body', field],
          msg: message,
          type: 'value_error',
        },
      ],
    },
  }
}

export function createMockUnauthorizedError(): { status: number; body: MockErrorResponse } {
  return {
    status: 401,
    body: { detail: 'Could not validate credentials' },
  }
}

export function createMockForbiddenError(): { status: number; body: MockErrorResponse } {
  return {
    status: 403,
    body: { detail: 'Not enough permissions' },
  }
}

export function createMockNotFoundError(resource = 'Resource'): { status: number; body: MockErrorResponse } {
  return {
    status: 404,
    body: { detail: `${resource} not found` },
  }
}

export function createMockServerError(): { status: number; body: MockErrorResponse } {
  return {
    status: 500,
    body: { detail: 'Internal server error' },
  }
}
