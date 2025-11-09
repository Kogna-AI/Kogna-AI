/**
 * Kogna-AI API Service
 * Frontend API client for communicating with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
import type { BackendUser } from "../app/components/auth/UserContext";
/**
 * Get authentication headers
 */
const getAuthHeaders = (): HeadersInit => {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;
  console.log(token);
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

/**
 * Handle API response
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ detail: "An error occurred" }));
    throw new Error(
      errorData.detail || `HTTP error! status: ${response.status}`
    );
  }
  // Try to parse JSON
  try {
    const data = await response.json();
    // FastAPI returns {success: true, data: {...}} or root data
    return data.data || data;
  } catch (e) {
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

  login: async (email: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    return handleResponse(response);
  },

  register: async (data: {
    email: string;
    password: string;
    first_name: string;
    second_name?: string;
    role?: string;
    organization_id: number;
  }) => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  getCurrentUser: async () => {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  // ==================== ORGANIZATIONS ====================

  getOrganization: async (orgId: number) => {
    const response = await fetch(`${API_BASE_URL}/organizations/${orgId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  listOrganizations: async () => {
    const response = await fetch(`${API_BASE_URL}/organizations`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  createOrganization: async (data: {
    name: string;
    industry?: string;
    team_due?: number;
    team?: string;
    project_number?: number;
  }) => {
    const response = await fetch(`${API_BASE_URL}/organizations`, {
      method: "POST",
      headers: getAuthHeaders(),
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
    const response = await fetch(`${API_BASE_URL}/organizations/${orgId}`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  // ==================== DASHBOARD ====================

  getDashboard: async (orgId: number) => {
    const response = await fetch(
      `${API_BASE_URL}/organizations/${orgId}/dashboard`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // ==================== USERS ====================

  getUser: async (userId: number) => {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  listOrganizationUsers: async (orgId: number) => {
    const response = await fetch(
      `${API_BASE_URL}/organizations/${orgId}/users`,
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
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  // ==================== TEAMS ====================

  getTeam: async (teamId: number) => {
    const response = await fetch(`${API_BASE_URL}/teams/${teamId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  listOrganizationTeams: async (orgId: number) => {
    const response = await fetch(
      `${API_BASE_URL}/organizations/${orgId}/teams`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  createTeam: async (data: { organization_id: number; name: string }) => {
    const response = await fetch(`${API_BASE_URL}/teams`, {
      method: "POST",
      headers: getAuthHeaders(),
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
    const response = await fetch(`${API_BASE_URL}/teams/members`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  // ==================== OBJECTIVES ====================

  getObjective: async (objId: number) => {
    const response = await fetch(`${API_BASE_URL}/objectives/${objId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  listObjectives: async (orgId: number, filters?: { status?: string }) => {
    const params = new URLSearchParams(filters as any).toString();
    const url = params
      ? `${API_BASE_URL}/organizations/${orgId}/objectives?${params}`
      : `${API_BASE_URL}/organizations/${orgId}/objectives`;

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
    const response = await fetch(`${API_BASE_URL}/objectives`, {
      method: "POST",
      headers: getAuthHeaders(),
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
    const response = await fetch(`${API_BASE_URL}/objectives/${objId}`, {
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
    const response = await fetch(`${API_BASE_URL}/growth-stages`, {
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
    const response = await fetch(`${API_BASE_URL}/milestones`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  achieveMilestone: async (milestoneId: number) => {
    const response = await fetch(
      `${API_BASE_URL}/milestones/${milestoneId}/achieve`,
      {
        method: "PUT",
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // ==================== METRICS ====================

  getMetric: async (metricId: number) => {
    const response = await fetch(`${API_BASE_URL}/metrics/${metricId}`, {
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
      ? `${API_BASE_URL}/organizations/${orgId}/metrics?${params}`
      : `${API_BASE_URL}/organizations/${orgId}/metrics`;

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
    const response = await fetch(`${API_BASE_URL}/metrics`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  getMetricTrends: async (orgId: number) => {
    const response = await fetch(
      `${API_BASE_URL}/organizations/${orgId}/metrics/trends`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // ==================== INSIGHTS ====================

  getInsight: async (insightId: number) => {
    const response = await fetch(`${API_BASE_URL}/insights/${insightId}`, {
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
    const params = new URLSearchParams(filters as any).toString();
    const url = params
      ? `${API_BASE_URL}/organizations/${orgId}/insights?${params}`
      : `${API_BASE_URL}/organizations/${orgId}/insights`;

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
    const response = await fetch(`${API_BASE_URL}/insights`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  archiveInsight: async (insightId: number) => {
    const response = await fetch(
      `${API_BASE_URL}/insights/${insightId}/archive`,
      {
        method: "PUT",
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  // ==================== RECOMMENDATIONS ====================

  getRecommendation: async (recId: number) => {
    const response = await fetch(`${API_BASE_URL}/recommendations/${recId}`, {
      headers: getAuthHeaders(),
    });
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
      ? `${API_BASE_URL}/organizations/${orgId}/recommendations?${params}`
      : `${API_BASE_URL}/organizations/${orgId}/recommendations`;

    const response = await fetch(url, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  getPendingRecommendations: async (orgId: number) => {
    const response = await fetch(
      `${API_BASE_URL}/organizations/${orgId}/recommendations/pending`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  getHighPriorityRecommendations: async (orgId: number) => {
    const response = await fetch(
      `${API_BASE_URL}/organizations/${orgId}/recommendations/high-priority`,
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
    const response = await fetch(`${API_BASE_URL}/recommendations`, {
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
    const response = await fetch(
      `${API_BASE_URL}/recommendations/${recId}/status?new_status=${status}`,
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
    const response = await fetch(`${API_BASE_URL}/recommendations/${recId}`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  deleteRecommendation: async (recId: number) => {
    const response = await fetch(`${API_BASE_URL}/recommendations/${recId}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  assignRecommendation: async (recId: number, userId: number) => {
    const response = await fetch(
      `${API_BASE_URL}/recommendations/${recId}/assign?user_id=${userId}`,
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
      evidence_datasets_id?: any;
    }
  ) => {
    const response = await fetch(
      `${API_BASE_URL}/recommendations/${recId}/reasons`,
      {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
      }
    );
    return handleResponse(response);
  },

  getRecommendationReasons: async (recId: number) => {
    const response = await fetch(
      `${API_BASE_URL}/recommendations/${recId}/reasons`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  getRecommendationStats: async (orgId: number) => {
    const response = await fetch(
      `${API_BASE_URL}/organizations/${orgId}/recommendations/stats`,
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
    const response = await fetch(`${API_BASE_URL}/actions`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  getRecommendationActions: async (recId: number) => {
    const response = await fetch(
      `${API_BASE_URL}/recommendations/${recId}/actions`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  getUserActions: async (userId: number, limit: number = 50) => {
    const response = await fetch(
      `${API_BASE_URL}/users/${userId}/actions?limit=${limit}`,
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
  startChatSession: async (): Promise<{id: string, user_id: string, title: string, created_at: string}> => {
    const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  /**
   * Gets a list of all past chat sessions for the authenticated user.
   * @returns {Promise<Array<{id: string, user_id: string, title: string, created_at: string}>>} A list of session objects.
   */
  getUserSessions: async (): Promise<Array<{id: string, user_id: string, title: string, created_at: string}>> => {
    const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
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
  getSessionHistory: async (sessionId: string): Promise<Array<{id: string, role: string, content: string, created_at: string}>> => {
    const response = await fetch(`${API_BASE_URL}/chat/history/${sessionId}`, {
      method: "GET",
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  /**
   * Sends a user's query to a specific chat session and gets the AI's response.
   * This is the main endpoint for sending and receiving messages.
   * The backend will automatically load history and save the new user/assistant messages.
   * @param sessionId - The UUID of the session.
   * @param userQuery - The user's new message.
   * @param executionMode - (Optional) "auto" or "micromanage".
   * @returns {Promise<{final_report: string, session_id: string, user_query: string}>} The AI's response.
   */
  runAgentInSession: async (
    sessionId: string,
    userQuery: string,
    executionMode: string = "auto"
  ): Promise<{final_report: string, session_id: string, user_query: string}> => {
    
    const payload = {
      session_id: sessionId,
      user_query: userQuery,
      execution_mode: executionMode,
    };

    const response = await fetch(`${API_BASE_URL}/api/ai/run`, {
      method: "POST",
      headers: getAuthHeaders(),
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
    const response = await fetch(`${API_BASE_URL}/health`);
    return handleResponse(response);
  },

  getUserBySupabaseId: async (supabaseId: string): Promise<BackendUser> => {
    const response = await fetch(
      `${API_BASE_URL}/api/users/by-supabase/${supabaseId}`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse<BackendUser>(response);
  },
<<<<<<<<< Temporary merge branch 1
  // ==================== CONNECTORS (GENERAL) ====================

  /**
   * Get authorization URL for any provider (Jira, Google, Slack, etc.)
   * Example: const { url } = await api.getConnectUrl("jira");
   */
  getConnectUrl: async (provider: string) => {
    const response = await fetch(`${API_BASE_URL}/connect/${provider}`, {
      headers: getAuthHeaders(),
    });
    const data = await response.json();
    window.location.href = data.url;
  },

  /**
   * Exchange OAuth code for access/refresh tokens (after redirect)
   * Example: await api.exchangeCode("jira", code);
   */
  exchangeCode: async (provider: string, code: string) => {
    const response = await fetch(
      `${API_BASE_URL}/auth/exchange/${provider}?code=${encodeURIComponent(
        code
      )}`,
      {
        method: "POST",
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },

  /**
   * Manually trigger ETL sync for a specific provider
   * Example: await api.manualSync("jira");
   */
  manualSync: async (provider: string) => {
=========

  // ==================== CONNECTORS ====================

  /**
   * Initiate OAuth flow for a connector
   * Redirects user to the provider's authorization page
   */
  connectProvider: (provider: string) => {
    // Connector routes are at /api/connect
    window.location.href = `${API_BASE_URL}/connect/${provider}`;
  },

  /**
   * Manually trigger sync for a connected provider
   */
  syncProvider: async (provider: string) => {
>>>>>>>>> Temporary merge branch 2
    const response = await fetch(`${API_BASE_URL}/connect/sync/${provider}`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  /**
<<<<<<<<< Temporary merge branch 1
   * (Optional) Get all connectors linked to the current user
   * Example: const connectors = await api.listConnections(userId);
   */
  listConnections: async (userId: string | number) => {
    const response = await fetch(`${API_BASE_URL}/users/${userId}/connectors`, {
      headers: getAuthHeaders(),
    });
    return handleResponse<
      {
        id: number;
        user_id: string;
        service: string;
        expires_at: number;
        created_at: string;
      }[]
    >(response);
  },

  /**
   * (Optional) Disconnect a specific connector
   * Example: await api.disconnect("jira");
   */
  disconnect: async (provider: string) => {
    const response = await fetch(
      `${API_BASE_URL}/connect/disconnect/${provider}`,
      {
        method: "DELETE",
=========
   * Get connection status for a provider
   */
  getConnectorStatus: async (provider: string) => {
    const response = await fetch(
      `${API_BASE_URL}/connectors/${provider}/status`,
      {
>>>>>>>>> Temporary merge branch 2
        headers: getAuthHeaders(),
      }
    );
    return handleResponse(response);
  },
<<<<<<<<< Temporary merge branch 1
=========

  /**
   * List all connected providers for current user
   */
  listConnectedProviders: async () => {
    const response = await fetch(`${API_BASE_URL}/connectors/connected`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },
>>>>>>>>> Temporary merge branch 2
};

export default api;