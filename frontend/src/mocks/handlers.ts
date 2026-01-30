/**
 * MSW (Mock Service Worker) request handlers for testing.
 *
 * These handlers intercept API requests during tests and return mock responses.
 * Add handlers for each API endpoint you want to mock.
 *
 * For test-specific overrides, use server.use() in individual tests:
 * @example
 * ```ts
 * import { server } from '@/test-utils'
 * import { errorHandlers } from '@/mocks/handlers'
 *
 * test('handles error', () => {
 *   server.use(errorHandlers.loginUnauthorized)
 *   // test error handling
 * })
 * ```
 */

import { http, HttpResponse, delay } from 'msw'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ==================== DEFAULT HANDLERS ====================

export const handlers = [
  // ==================== AUTH ENDPOINTS ====================

  http.post(`${API_URL}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string }

    if (body.email === 'test@example.com' && body.password === 'password123') {
      return HttpResponse.json({
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        user: {
          id: 'user-123',
          email: body.email,
          first_name: 'Test',
          second_name: 'User',
          organization_id: 'org-123',
        },
      })
    }

    return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 })
  }),

  http.post(`${API_URL}/auth/register`, async ({ request }) => {
    const body = (await request.json()) as {
      email: string
      password: string
      first_name: string
      second_name: string
    }

    // Check for existing email (for testing duplicate email handling)
    if (body.email === 'existing@example.com') {
      return HttpResponse.json(
        { detail: 'Email already registered' },
        { status: 400 }
      )
    }

    return HttpResponse.json(
      {
        id: 'user-new-123',
        email: body.email,
        first_name: body.first_name,
        second_name: body.second_name,
        organization_id: null,
      },
      { status: 201 }
    )
  }),

  http.post(`${API_URL}/auth/refresh`, async () => {
    return HttpResponse.json({
      access_token: 'new-mock-access-token',
    })
  }),

  http.post(`${API_URL}/auth/logout`, async () => {
    return HttpResponse.json({ message: 'Logged out successfully' })
  }),

  http.post(`${API_URL}/auth/forgot-password`, async ({ request }) => {
    const body = (await request.json()) as { email: string }
    return HttpResponse.json({
      message: `Password reset email sent to ${body.email}`,
    })
  }),

  // ==================== USER ENDPOINTS ====================

  http.get(`${API_URL}/users/me`, async () => {
    return HttpResponse.json({
      id: 'user-123',
      email: 'test@example.com',
      first_name: 'Test',
      second_name: 'User',
      organization_id: 'org-123',
      role: 'member',
    })
  }),

  http.patch(`${API_URL}/users/me`, async ({ request }) => {
    const body = (await request.json()) as Partial<{
      first_name: string
      second_name: string
      email: string
    }>
    return HttpResponse.json({
      id: 'user-123',
      email: body.email || 'test@example.com',
      first_name: body.first_name || 'Test',
      second_name: body.second_name || 'User',
      organization_id: 'org-123',
      role: 'member',
    })
  }),

  // ==================== KPI ENDPOINTS ====================

  http.get(`${API_URL}/kpis`, async () => {
    return HttpResponse.json([
      {
        id: 'kpi-1',
        name: 'Monthly Revenue',
        value: 150000,
        unit: 'USD',
        trend: 5.2,
        trend_direction: 'up',
        period: '2024-01',
      },
      {
        id: 'kpi-2',
        name: 'Active Users',
        value: 5000,
        unit: 'count',
        trend: 12.1,
        trend_direction: 'up',
        period: '2024-01',
      },
      {
        id: 'kpi-3',
        name: 'Customer Satisfaction',
        value: 4.5,
        unit: 'rating',
        trend: 2.3,
        trend_direction: 'up',
        period: '2024-01',
      },
    ])
  }),

  http.get(`${API_URL}/kpis/dashboard`, async () => {
    return HttpResponse.json({
      kpis: [
        {
          id: 'kpi-1',
          name: 'Monthly Revenue',
          value: 150000,
          unit: 'USD',
          trend: 5.2,
          period: '2024-01',
        },
        {
          id: 'kpi-2',
          name: 'Active Users',
          value: 5000,
          unit: 'count',
          trend: 12.1,
          period: '2024-01',
        },
        {
          id: 'kpi-3',
          name: 'Customer Satisfaction',
          value: 4.5,
          unit: 'rating',
          trend: 2.3,
          period: '2024-01',
        },
      ],
      summary: {
        total_kpis: 3,
        positive_trends: 3,
        negative_trends: 0,
      },
    })
  }),

  http.get(`${API_URL}/kpis/:id`, async ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: 'Monthly Revenue',
      value: 150000,
      unit: 'USD',
      trend: 5.2,
      trend_direction: 'up',
      period: '2024-01',
      history: [
        { period: '2023-10', value: 130000 },
        { period: '2023-11', value: 138000 },
        { period: '2023-12', value: 142000 },
        { period: '2024-01', value: 150000 },
      ],
    })
  }),

  // ==================== TEAM ENDPOINTS ====================

  http.get(`${API_URL}/teams`, async () => {
    return HttpResponse.json([
      {
        id: 'team-1',
        name: 'Engineering',
        organization_id: 'org-123',
        members_count: 10,
      },
      {
        id: 'team-2',
        name: 'Product',
        organization_id: 'org-123',
        members_count: 5,
      },
      {
        id: 'team-3',
        name: 'Design',
        organization_id: 'org-123',
        members_count: 3,
      },
    ])
  }),

  http.get(`${API_URL}/teams/:id`, async ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: 'Engineering',
      organization_id: 'org-123',
      members_count: 10,
      members: [
        { id: 'user-1', name: 'John Doe', role: 'lead' },
        { id: 'user-2', name: 'Jane Smith', role: 'member' },
      ],
    })
  }),

  http.post(`${API_URL}/teams`, async ({ request }) => {
    const body = (await request.json()) as { name: string; organization_id: string }

    return HttpResponse.json(
      {
        id: 'team-new-123',
        name: body.name,
        organization_id: body.organization_id,
        members_count: 0,
      },
      { status: 201 }
    )
  }),

  http.patch(`${API_URL}/teams/:id`, async ({ params, request }) => {
    const body = (await request.json()) as Partial<{ name: string }>
    return HttpResponse.json({
      id: params.id,
      name: body.name || 'Engineering',
      organization_id: 'org-123',
      members_count: 10,
    })
  }),

  http.delete(`${API_URL}/teams/:id`, async () => {
    return HttpResponse.json({ message: 'Team deleted successfully' })
  }),

  // ==================== OBJECTIVES ENDPOINTS ====================

  http.get(`${API_URL}/objectives`, async () => {
    return HttpResponse.json([
      {
        id: 'obj-1',
        name: 'Increase Revenue',
        description: 'Increase quarterly revenue by 20%',
        status: 'in_progress',
        progress: 45.5,
        due_date: '2024-03-31',
      },
      {
        id: 'obj-2',
        name: 'Improve Customer Satisfaction',
        description: 'Reach NPS score of 50+',
        status: 'on_track',
        progress: 72.0,
        due_date: '2024-06-30',
      },
    ])
  }),

  http.get(`${API_URL}/objectives/:id`, async ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: 'Increase Revenue',
      description: 'Increase quarterly revenue by 20%',
      status: 'in_progress',
      progress: 45.5,
      due_date: '2024-03-31',
      key_results: [
        { id: 'kr-1', name: 'Acquire 10 new customers', progress: 50 },
        { id: 'kr-2', name: 'Increase upsell by 15%', progress: 35 },
      ],
    })
  }),

  http.post(`${API_URL}/objectives`, async ({ request }) => {
    const body = (await request.json()) as {
      name: string
      description: string
      due_date: string
    }
    return HttpResponse.json(
      {
        id: 'obj-new-123',
        ...body,
        status: 'not_started',
        progress: 0,
      },
      { status: 201 }
    )
  }),

  // ==================== INSIGHTS ENDPOINTS ====================

  http.get(`${API_URL}/insights`, async () => {
    return HttpResponse.json([
      {
        id: 'insight-1',
        title: 'Revenue Growth Opportunity',
        content: 'Analysis shows potential for 15% growth in Q2',
        category: 'revenue',
        priority: 'high',
        created_at: '2024-01-15T10:00:00Z',
      },
      {
        id: 'insight-2',
        title: 'Team Velocity Improvement',
        content: 'Sprint velocity has increased by 20% over the last month',
        category: 'performance',
        priority: 'medium',
        created_at: '2024-01-14T09:00:00Z',
      },
    ])
  }),

  http.get(`${API_URL}/insights/:id`, async ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      title: 'Revenue Growth Opportunity',
      content: 'Analysis shows potential for 15% growth in Q2',
      category: 'revenue',
      priority: 'high',
      created_at: '2024-01-15T10:00:00Z',
      recommendations: [
        'Focus on enterprise segment',
        'Increase marketing spend',
      ],
    })
  }),

  // ==================== CONNECTORS ENDPOINTS ====================

  http.get(`${API_URL}/connectors`, async () => {
    return HttpResponse.json([
      {
        id: 'conn-1',
        type: 'jira',
        name: 'Jira',
        status: 'connected',
        last_sync: '2024-01-15T12:00:00Z',
      },
      {
        id: 'conn-2',
        type: 'google_drive',
        name: 'Google Drive',
        status: 'disconnected',
        last_sync: null,
      },
    ])
  }),

  http.get(`${API_URL}/connectors/status`, async () => {
    return HttpResponse.json([
      {
        id: 'conn-1',
        type: 'jira',
        name: 'Jira',
        status: 'connected',
        last_sync: '2024-01-15T12:00:00Z',
      },
      {
        id: 'conn-2',
        type: 'google_drive',
        name: 'Google Drive',
        status: 'disconnected',
        last_sync: null,
      },
    ])
  }),

  http.post(`${API_URL}/connectors/:type/connect`, async ({ params }) => {
    return HttpResponse.json({
      id: `conn-${params.type}`,
      type: params.type,
      status: 'connected',
      message: 'Successfully connected',
    })
  }),

  http.post(`${API_URL}/connectors/:type/sync`, async ({ params }) => {
    return HttpResponse.json({
      id: `conn-${params.type}`,
      type: params.type,
      status: 'syncing',
      message: 'Sync started',
    })
  }),

  // ==================== CHAT ENDPOINTS ====================

  http.post(`${API_URL}/chat/message`, async ({ request }) => {
    const body = (await request.json()) as {
      message: string
      conversation_id?: string
    }

    // Add a small delay to simulate network latency
    await delay(100)

    return HttpResponse.json({
      id: 'msg-123',
      role: 'assistant',
      content: `I received your message: "${body.message}". How can I help you further?`,
      conversation_id: body.conversation_id || 'conv-new-123',
      created_at: new Date().toISOString(),
    })
  }),

  http.get(`${API_URL}/chat/conversations`, async () => {
    return HttpResponse.json([
      {
        id: 'conv-1',
        title: 'Revenue Analysis',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:30:00Z',
      },
      {
        id: 'conv-2',
        title: 'Team Performance Review',
        created_at: '2024-01-14T09:00:00Z',
        updated_at: '2024-01-14T09:45:00Z',
      },
    ])
  }),

  http.get(`${API_URL}/chat/conversations/:id`, async ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      title: 'Revenue Analysis',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:30:00Z',
      messages: [
        {
          id: 'msg-1',
          role: 'user',
          content: 'What was our revenue last month?',
          created_at: '2024-01-15T10:00:00Z',
        },
        {
          id: 'msg-2',
          role: 'assistant',
          content: 'Your revenue last month was $150,000, up 5.2% from the previous month.',
          created_at: '2024-01-15T10:00:05Z',
        },
      ],
    })
  }),

  http.delete(`${API_URL}/chat/conversations/:id`, async () => {
    return HttpResponse.json({ message: 'Conversation deleted' })
  }),

  // ==================== ORGANIZATION ENDPOINTS ====================

  http.get(`${API_URL}/organizations/current`, async () => {
    return HttpResponse.json({
      id: 'org-123',
      name: 'Acme Corporation',
      industry: 'Technology',
      created_at: '2024-01-01T00:00:00Z',
    })
  }),

  http.patch(`${API_URL}/organizations/current`, async ({ request }) => {
    const body = (await request.json()) as Partial<{ name: string; industry: string }>
    return HttpResponse.json({
      id: 'org-123',
      name: body.name || 'Acme Corporation',
      industry: body.industry || 'Technology',
      created_at: '2024-01-01T00:00:00Z',
    })
  }),
]

// ==================== ERROR HANDLERS ====================
// Use these handlers with server.use() in individual tests to simulate errors

export const errorHandlers = {
  // Auth errors
  loginUnauthorized: http.post(`${API_URL}/auth/login`, async () => {
    return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 })
  }),

  loginServerError: http.post(`${API_URL}/auth/login`, async () => {
    return HttpResponse.json({ detail: 'Internal server error' }, { status: 500 })
  }),

  // User errors
  userUnauthorized: http.get(`${API_URL}/users/me`, async () => {
    return HttpResponse.json({ detail: 'Could not validate credentials' }, { status: 401 })
  }),

  // KPI errors
  kpisServerError: http.get(`${API_URL}/kpis/dashboard`, async () => {
    return HttpResponse.json({ detail: 'Failed to fetch KPIs' }, { status: 500 })
  }),

  kpisNotFound: http.get(`${API_URL}/kpis/:id`, async () => {
    return HttpResponse.json({ detail: 'KPI not found' }, { status: 404 })
  }),

  // Team errors
  teamNotFound: http.get(`${API_URL}/teams/:id`, async () => {
    return HttpResponse.json({ detail: 'Team not found' }, { status: 404 })
  }),

  teamForbidden: http.delete(`${API_URL}/teams/:id`, async () => {
    return HttpResponse.json({ detail: 'Not enough permissions' }, { status: 403 })
  }),

  // Chat errors
  chatRateLimited: http.post(`${API_URL}/chat/message`, async () => {
    return HttpResponse.json(
      { detail: 'Too many requests. Please try again later.' },
      { status: 429 }
    )
  }),

  // Generic network error
  networkError: http.get('*', async () => {
    throw new Error('Network error')
  }),
}

// ==================== LOADING STATE HANDLERS ====================
// Use these to test loading states by adding artificial delay

export const loadingHandlers = {
  slowKPIs: http.get(`${API_URL}/kpis/dashboard`, async () => {
    await delay(2000)
    return HttpResponse.json({
      kpis: [],
      summary: { total_kpis: 0, positive_trends: 0, negative_trends: 0 },
    })
  }),

  slowChat: http.post(`${API_URL}/chat/message`, async () => {
    await delay(3000)
    return HttpResponse.json({
      id: 'msg-slow',
      role: 'assistant',
      content: 'Slow response',
      conversation_id: 'conv-1',
      created_at: new Date().toISOString(),
    })
  }),
}

// ==================== EMPTY STATE HANDLERS ====================
// Use these to test empty state UI

export const emptyHandlers = {
  noKPIs: http.get(`${API_URL}/kpis/dashboard`, async () => {
    return HttpResponse.json({
      kpis: [],
      summary: { total_kpis: 0, positive_trends: 0, negative_trends: 0 },
    })
  }),

  noTeams: http.get(`${API_URL}/teams`, async () => {
    return HttpResponse.json([])
  }),

  noInsights: http.get(`${API_URL}/insights`, async () => {
    return HttpResponse.json([])
  }),

  noConversations: http.get(`${API_URL}/chat/conversations`, async () => {
    return HttpResponse.json([])
  }),
}
