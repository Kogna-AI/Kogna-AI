/**
 * MSW (Mock Service Worker) request handlers for testing.
 *
 * These handlers intercept API requests during tests and return mock responses.
 * Add handlers for each API endpoint you want to mock.
 */

import { http, HttpResponse } from 'msw'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const handlers = [
  // ==================== AUTH ENDPOINTS ====================

  http.post(`${API_URL}/auth/login`, async ({ request }) => {
    const body = await request.json() as { email: string; password: string }

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

    return HttpResponse.json(
      { detail: 'Invalid credentials' },
      { status: 401 }
    )
  }),

  http.post(`${API_URL}/auth/register`, async ({ request }) => {
    const body = await request.json() as {
      email: string
      password: string
      first_name: string
      second_name: string
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

  // ==================== KPI ENDPOINTS ====================

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

  http.post(`${API_URL}/teams`, async ({ request }) => {
    const body = await request.json() as { name: string; organization_id: string }

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

  // ==================== CONNECTORS ENDPOINTS ====================

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

  // ==================== CHAT ENDPOINTS ====================

  http.post(`${API_URL}/chat/message`, async ({ request }) => {
    const body = await request.json() as { message: string; conversation_id?: string }

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
]
