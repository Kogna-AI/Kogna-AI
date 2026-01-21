/**
 * Kogna-AI API Service
 * Secure authentication with httpOnly cookies and in-memory access tokens
 */

import type { BackendUser } from "../app/components/auth/UserContext";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// AWS: Request timeout configuration
const REQUEST_TIMEOUT = 120000; // 120 seconds

/**
 * Fetch with timeout for AWS reliability
 * Prevents hanging requests in AWS infrastructure
 */
const fetchWithTimeout = async (
  url: string,
  options: RequestInit = {},
  timeout: number = REQUEST_TIMEOUT
): Promise<Response> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Request timeout - please try again");
    }
    throw error;
  }
};

// ==================== SECURE TOKEN STORAGE ====================
// Access token stored in memory only (never localStorage)
let inMemoryAccessToken: string | null = null;

export const setAccessToken = (token: string | null) => {
  inMemoryAccessToken = token;
};

export const getAccessToken = (): string | null => {
  return inMemoryAccessToken;
};

const getAuthHeaders = (): HeadersInit => {
  return {
    "Content-Type": "application/json",
    ...(inMemoryAccessToken && {
      Authorization: `Bearer ${inMemoryAccessToken}`,
    }),
  };
};

// ==================== AUTOMATIC TOKEN REFRESH ====================
let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        setAccessToken(null);
        throw new Error("Session expired");
      }

      const data = await response.json();
      const newToken = data.access_token || data.data?.access_token;

      if (!newToken) {
        throw new Error("No access token in refresh response");
      }

      setAccessToken(newToken);
      return newToken;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

async function secureFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const fetchOptions: RequestInit = {
    ...options,
    credentials: "include",
    headers: {
      ...getAuthHeaders(),
      ...options.headers,
    },
  };

  let response = await fetchWithTimeout(url, fetchOptions);

  // Auto-refresh on 401
  if (response.status === 401 && !isRefreshing) {
    try {
      const newToken = await refreshAccessToken();
      const retryOptions: RequestInit = {
        ...options,
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${newToken}`,
          ...options.headers,
        },
      };
      response = await fetchWithTimeout(url, retryOptions);
    } catch {
      // Refresh failed, propagate 401
    }
  }

  return response;
}

/**
 * Handle API response with AWS-specific error handling
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ detail: "An error occurred" }));

    // AWS-specific error handling
    if (response.status === 502) {
      throw new Error("Service temporarily unavailable. Please try again.");
    }
    if (response.status === 504) {
      throw new Error("Request timeout. Please try again.");
    }
    if (response.status === 503) {
      throw new Error("Service unavailable. Please try again later.");
    }

    throw new Error(
      errorData.detail || `HTTP error! status: ${response.status}`
    );
  }

  // Try to parse JSON
  try {
    const data = await response.json();
    // FastAPI returns {success: true, data: {...}} or root data
    return data.data || data;
  } catch (_e) {
    // Handle empty response for methods like DELETE
    if (response.status === 204 || response.status === 200) {
      return {} as T;
    }
    throw new Error("Failed to parse JSON response.");
  }
}

/**
 * API client
 */
export const api = {
  // ==================== AUTHENTICATION ====================

  // ==================== AUTHENTICATION (JWT ONLY) ====================

  login: async (email: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      credentials: "include", // Send/receive cookies
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await handleResponse<{
      access_token: string;
      user: any;
    }>(response);

    // Store access token in memory only
    if (data.access_token) {
      setAccessToken(data.access_token);
    }

    return data;
  },

  register: async (data: {
    email: string;
    password: string;
    first_name: string;
    second_name?: string;
    role?: string;
    organization: string;
  }) => {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    return handleResponse<{
      user_id: string;
      organization_id: string;
    }>(response);
  },

  getCurrentUser: async () => {
    const response = await secureFetch(`${API_BASE_URL}/api/auth/me`, {
      method: "GET",
    });
    return handleResponse(response);
  },

  logout: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });
      await handleResponse(response);
    } finally {
      // Always clear in-memory token
      setAccessToken(null);
    }
  },

  refreshToken: async () => {
    return refreshAccessToken();
  },

  // ==================== ORGANIZATIONS ====================

  getOrganization: async (orgId: number) => {
    const response = await secureFetch(
      `${API_BASE_URL}/api/organizations/${orgId}`
    );
    return handleResponse(response);
  },

  listOrganizations: async () => {
    const response = await secureFetch(`${API_BASE_URL}/api/organizations`);
    return handleResponse(response);
  },

  createOrganization: async (data: {
    name: string;
    industry?: string;
    team_due?: number;
    team?: string;
    project_number?: number;
  }) => {
    const response = await secureFetch(`${API_BASE_URL}/api/organizations`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  updateOrganization: async (
    orgId: number,
    data: {
      name: string;
      industry?: string;
      team_due?: number;
      team?: string;
      project_number?: number;
    }
  ) => {
    const response = await fetch(`${API_BASE_URL}/api/organizations/${orgId}`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  // ==================== DASHBOARD ====================

  getDashboard: async (orgId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/organizations/${orgId}/dashboard`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // ==================== USERS ====================

  getUser: async (userId: number) => {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },
  listVisibleUsers: async () => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/users/visible`,
      {
        method: "GET",
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },
  listOrganizationUsers: async (orgId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/organizations/${orgId}/users`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  updateUser: async (
    userId: number,
    data: {
      organization_id: number;
      first_name: string;
      second_name?: string;
      role?: string;
      email: string;
    }
  ) => {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  // ==================== TEAMS ====================

  getTeam: async (teamId: number | string) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/teams/${teamId}`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // List all members in a team by team_id
  listTeamMembers: async (teamId: number | string) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/teams/${teamId}/members`,
      {
        method: "GET",
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  removeTeamMember: async (teamId: string, userId: string) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/teams/${teamId}/members/${userId}`,
      {
        method: "DELETE",
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // Hierarchical team view for TeamOverview
  teamHierarchy: async () => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/teams/hierarchy`,
      {
        method: "GET",
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  createTeam: async (data: { organization_id: string; name: string }) => {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/teams`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  addTeamMember: async (data: {
    team_id: number;
    user_id: number;
    role?: string;
    performance?: number;
    capacity?: number;
  }) => {
    const response = await fetch(`${API_BASE_URL}/api/teams/members`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  // Invitations
  createTeamInvitation: async (
    teamId: string,
    data: { email: string; role?: string; team_ids?: string[] }
  ) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/teams/${teamId}/invitations`,
      {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
      }
    );
    return handleResponse<{
      id: string;
      email: string;
      token: string;
      expires_at: string;
    }>(response);
  },

  getTeamInvitation: async (
    token: string
  ): Promise<{
    email: string;
    organization_name: string;
    team_name: string;
  }> => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/teams/invitations/${token}`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  acceptTeamInvitation: async (
    token: string,
    data: { first_name: string; second_name?: string; password: string }
  ) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/teams/invitations/${token}/accept`,
      {
        method: "POST",
        headers: await getAuthHeaders(),
        body: JSON.stringify(data),
      }
    );
    return handleResponse<{
      user_id: string;
      organization_id: string;
      team_id: string;
    }>(response);
  },

  // Get user's team (first team they belong to)
  getUserTeam: async (userId: string) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/teams/user/${userId}`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // List all teams in an organization
  listOrganizationTeams: async (orgId: string, excludeCeoTeams?: boolean) => {
    const url = new URL(`${API_BASE_URL}/api/teams/organization/${orgId}`);
    if (excludeCeoTeams) {
      url.searchParams.append("exclude_ceo_teams", "true");
    }
    const response = await fetchWithTimeout(url.toString(), {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  // ==================== OBJECTIVES ====================

  getObjective: async (objId: number) => {
    const response = await fetch(`${API_BASE_URL}/api/objectives/${objId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  listObjectives: async (orgId: number, filters?: { status?: string }) => {
    const params = new URLSearchParams(
      filters as Record<string, string>
    ).toString();
    const url = params
      ? `${API_BASE_URL}/api/organizations/${orgId}/objectives?${params}`
      : `${API_BASE_URL}/api/organizations/${orgId}/objectives`;

    const response = await fetch(url, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  createObjective: async (data: {
    organization_id: number;
    title: string;
    progress?: number;
    status?: string;
    team_responsible?: string;
  }) => {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/objectives`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  updateObjective: async (
    objId: number,
    data: {
      title?: string;
      progress?: number;
      status?: string;
      team_responsible?: string;
    }
  ) => {
    const response = await fetch(`${API_BASE_URL}/api/objectives/${objId}`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  createGrowthStage: async (data: {
    objective_id: number;
    name: string;
    description?: string;
    start_date?: string;
    end_date?: string;
  }) => {
    const response = await fetch(`${API_BASE_URL}/api/growth-stages`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  createMilestone: async (data: {
    growth_stage_id: number;
    title: string;
    achieved?: boolean;
  }) => {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/milestones`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  achieveMilestone: async (milestoneId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/milestones/${milestoneId}/achieve`,
      {
        method: "PUT",
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // ==================== METRICS ====================

  getMetric: async (metricId: number) => {
    const response = await fetch(`${API_BASE_URL}/api/metrics/${metricId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  listMetrics: async (
    orgId: number,
    filters?: { name?: string; limit?: number }
  ) => {
    const params = new URLSearchParams({
      ...(filters?.name && { name: filters.name }),
      ...(filters?.limit && { limit: filters.limit.toString() }),
    }).toString();

    const url = params
      ? `${API_BASE_URL}/api/organizations/${orgId}/metrics?${params}`
      : `${API_BASE_URL}/api/organizations/${orgId}/metrics`;

    const response = await fetch(url, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  createMetric: async (data: {
    organization_id: number;
    name: string;
    value: number;
    unit?: string;
    change_from_last?: number;
  }) => {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/metrics`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  getMetricTrends: async (orgId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/organizations/${orgId}/metrics/trends`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // ==================== INSIGHTS ====================

  getInsight: async (insightId: number) => {
    const response = await fetch(`${API_BASE_URL}/api/insights/${insightId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  listInsights: async (
    orgId: number,
    filters?: {
      category?: string;
      level?: string;
      status?: string;
    }
  ) => {
    const params = new URLSearchParams(
      filters as Record<string, string>
    ).toString();
    const url = params
      ? `${API_BASE_URL}/api/organizations/${orgId}/insights?${params}`
      : `${API_BASE_URL}/api/organizations/${orgId}/insights`;

    const response = await fetch(url, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  createInsight: async (data: {
    organization_id: number;
    category: string;
    title: string;
    description: string;
    confidence: number;
    level: string;
  }) => {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/insights`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  archiveInsight: async (insightId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/insights/${insightId}/archive`,
      {
        method: "PUT",
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // ==================== RECOMMENDATIONS ====================

  getRecommendation: async (recId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/recommendations/${recId}`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  listRecommendations: async (
    orgId: number,
    filters?: {
      status?: string;
      created_for?: number;
      min_confidence?: number;
    }
  ) => {
    const params = new URLSearchParams();
    if (filters?.status) params.append("status", filters.status);
    if (filters?.created_for)
      params.append("created_for", filters.created_for.toString());
    if (filters?.min_confidence)
      params.append("min_confidence", filters.min_confidence.toString());

    const url = params.toString()
      ? `${API_BASE_URL}/api/organizations/${orgId}/recommendations?${params}`
      : `${API_BASE_URL}/api/organizations/${orgId}/recommendations`;

    const response = await fetch(url, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  getPendingRecommendations: async (orgId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/organizations/${orgId}/recommendations/pending`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  getHighPriorityRecommendations: async (orgId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/organizations/${orgId}/recommendations/high-priority`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  createRecommendation: async (data: {
    organization_id: number;
    title: string;
    recommendation: string;
    confidence: number;
    action?: string;
    created_for?: number;
  }) => {
    const response = await fetch(`${API_BASE_URL}/api/recommendations`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  updateRecommendationStatus: async (
    recId: number,
    status: "pending" | "acted" | "dismissed"
  ) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/recommendations/${recId}/status?new_status=${status}`,
      {
        method: "PUT",
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  updateRecommendation: async (
    recId: number,
    data: {
      organization_id: number;
      title: string;
      recommendation: string;
      confidence: number;
      action?: string;
      created_for?: number;
    }
  ) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/recommendations/${recId}`,
      {
        method: "PUT",
        headers: await getAuthHeaders(),
        body: JSON.stringify(data),
      }
    );
    return handleResponse(response);
  },

  deleteRecommendation: async (recId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/recommendations/${recId}`,
      {
        method: "DELETE",
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  assignRecommendation: async (recId: number, userId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/recommendations/${recId}/assign?user_id=${userId}`,
      {
        method: "POST",
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  addRecommendationReason: async (
    recId: number,
    data: {
      recommendation_id: number;
      reason: string;
      evidence_datasets_id?: number | null;
    }
  ) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/recommendations/${recId}/reasons`,
      {
        method: "POST",
        headers: await getAuthHeaders(),
        body: JSON.stringify(data),
      }
    );
    return handleResponse(response);
  },

  getRecommendationReasons: async (recId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/recommendations/${recId}/reasons`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  getRecommendationStats: async (orgId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/organizations/${orgId}/recommendations/stats`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // ==================== ACTIONS ====================

  createAction: async (data: {
    user_id: number;
    recommendation_id?: number;
    action_taken: string;
    result?: string;
  }) => {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/actions`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  getRecommendationActions: async (recId: number) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/recommendations/${recId}/actions`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  getUserActions: async (userId: number, limit: number = 50) => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/users/${userId}/actions?limit=${limit}`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // ================================================
  // ===== CHATBOT & AI (STATEFUL) - UPDATED =====
  // ================================================

  /**
   * Starts a new chat session for the authenticated user.
   * This is the first call to make when a user starts a new chat.
   * @returns {Promise<{id: string, user_id: string, title: string, created_at: string}>} The new session object.
   */
  startChatSession: async (): Promise<{
    id: string;
    user_id: string;
    title: string;
    created_at: string;
  }> => {
    const response = await fetch(`${API_BASE_URL}/api/chat/sessions`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  /**
   * Gets a list of all past chat sessions for the authenticated user.
   * @returns {Promise<Array<{id: string, user_id: string, title: string, created_at: string}>>} A list of session objects.
   */
  getUserSessions: async (): Promise<
    Array<{ id: string; user_id: string; title: string; created_at: string }>
  > => {
    const response = await fetch(`${API_BASE_URL}/api/chat/sessions`, {
      method: "GET",
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  /**
   * Gets all messages for a specific chat session.
   * Call this when a user clicks on an old conversation to load its history.
   * @param sessionId - The UUID of the chat session.
   * @returns {Promise<Array<{id: string, role: string, content: string, created_at: string}>>} A list of message objects.
   */
  getSessionHistory: async (
    sessionId: string
  ): Promise<
    Array<{ id: string; role: string; content: string; created_at: string }>
  > => {
    const response = await fetch(`${API_BASE_URL}/chat/history/${sessionId}`, {
      method: "GET",
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  runAgentInSession: async (
    sessionId: string,
    userQuery: string,
    executionMode: string = "auto"
  ): Promise<{
    final_report: string;
    session_id: string;
    user_query: string;
  }> => {
    const payload = {
      session_id: sessionId,
      user_query: userQuery,
      execution_mode: executionMode,
    };

    const response = await fetchWithTimeout(`${API_BASE_URL}/api/chat/run`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify(payload),
    });

    // This endpoint returns data at the root, so we handle it directly
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "An error occurred" }));
      throw new Error(
        errorData.detail || `HTTP error! status: ${response.status}`
      );
    }
    return response.json();
  },

  // ==================== HEALTH CHECK ====================

  healthCheck: async () => {
    // Note: Verify this path matches your backend
    // If your backend has /api/health instead, change this to: `${API_BASE_URL}/api/health`
    const response = await fetchWithTimeout(`${API_BASE_URL}/health`);
    return handleResponse(response);
  },

  getUserBySupabaseId: async (supabaseId: string): Promise<BackendUser> => {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/users/by-supabase/${supabaseId}`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse<BackendUser>(response);
  },

  // ==================== CONNECTORS (GENERAL) ====================

  getConnectUrl: async (provider: string) => {
    try {
      const response = await fetchWithTimeout(
        `${API_BASE_URL}/api/connect/${provider}`,
        {
          headers: getAuthHeaders(),
        }
      );

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Failed to get connect URL" }));
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();

      if (!data.url) {
        throw new Error("No authorization URL returned from server");
      }

      return data;
    } catch (error) {
      console.error(`Error getting ${provider} connect URL:`, error);
      throw error;
    }
  },

  handleOAuthCallback: async (provider: string, code: string) => {
    try {
      if (!code) {
        throw new Error("No authorization code received");
      }

      const response = await fetchWithTimeout(
        `${API_BASE_URL}/api/auth/exchange/${provider}?code=${encodeURIComponent(
          code
        )}`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );

      return handleResponse(response);
    } catch (error) {
      console.error(`Error handling ${provider} OAuth callback:`, error);
      throw error;
    }
  },

  exchangeCode: async (provider: string, code: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/auth/exchange/${provider}?code=${encodeURIComponent(
          code
        )}`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );
      return handleResponse(response);
    } catch (error) {
      console.error(`Error exchanging ${provider} code:`, error);
      throw error;
    }
  },

  manualSync: async (provider: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/connect/sync/${provider}`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );
      return handleResponse(response);
    } catch (error) {
      console.error(`Error syncing ${provider}:`, error);
      throw error;
    }
  },

  listConnections: async (userId: string | number) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/users/${userId}/connectors`,
        {
          headers: getAuthHeaders(),
        }
      );
      return handleResponse<
        {
          id: number;
          user_id: string;
          service: string;
          expires_at: number;
          created_at: string;
        }[]
      >(response);
    } catch (error) {
      console.error("Error listing connections:", error);
      throw error;
    }
  },

  disconnect: async (provider: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/connect/disconnect/${provider}`,
        {
          method: "DELETE",
          headers: getAuthHeaders(),
        }
      );
      return handleResponse(response);
    } catch (error) {
      console.error(`Error disconnecting ${provider}:`, error);
      throw error;
    }
  },

  // Add this to check connection status
  checkConnectionStatus: async (provider: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/connect/status/${provider}`,
        {
          headers: getAuthHeaders(),
        }
      );
      return handleResponse<{ connected: boolean; expires_at?: number }>(
        response
      );
    } catch (error) {
      console.error(`Error checking ${provider} connection status:`, error);
      throw error;
    }
  },
};

export default api;
