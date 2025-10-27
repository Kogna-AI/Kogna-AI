/**
 * Kogna-AI API Service
 * Frontend API client for communicating with the FastAPI backend
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
import type { BackendUser } from "../app/components/auth/UserContext";
/**
 * Get authentication headers
 */
const getAuthHeaders = (): HeadersInit => {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;
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
  const data = await response.json();
  // FastAPI returns {success: true, data: {...}}
  return data.data || data;
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

  // createUser: async (data: {
  //   organization_id: number;
  //   first_name: string;
  //   second_name?: string;
  //   role?: string;
  //   email: string;
  // }) => {
  //   const response = await fetch(`${API_BASE_URL}/users`, {
  //     method: "POST",
  //     headers: getAuthHeaders(),
  //     body: JSON.stringify(data),
  //   });
  //   return handleResponse(response);
  // },

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

  // ==================== KOGNII AI ====================

  /**
   * Run the main Kogna AI orchestration pipeline
   */
  runAiWorkflow: async (
    userQuery: string,
    chatHistory: { role: "user" | "assistant" | "system"; content: string }[],
    executionMode: string = "autonomous"
  ): Promise<{
    success: boolean;
    user_query: string;
    execution_mode: string;
    final_report: string;
  }> => {
    const payload = {
      user_query: userQuery,
      chat_history: chatHistory,
      execution_mode: executionMode,
    };

    const response = await fetch(`${API_BASE_URL}/ai/run`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });

    // We handle this response directly instead of using handleResponse
    // because the AI endpoint returns data at the root, not in a 'data' field.
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "An error occurred" }));
      throw new Error(
        errorData.detail || `HTTP error! status: ${response.status}`
      );
    }

    // The response is { success: true, final_report: "...", ... }
    return response.json();
  },

  // ==================== HEALTH CHECK ====================

  healthCheck: async () => {
    const response = await fetch(`${API_BASE_URL}/health`);
    return handleResponse(response);
  },

  getUserBySupabaseId: async (supabaseId: string): Promise<BackendUser> => {
    const response = await fetch(
      `${API_BASE_URL}/users/by-supabase/${supabaseId}`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse<BackendUser>(response); // ✅ tell TS this returns BackendUser
  },
};

export default api;
