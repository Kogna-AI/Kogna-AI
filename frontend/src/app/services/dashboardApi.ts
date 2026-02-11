import type {
  DashboardResponse,
  MetricsResponse,
  InsightsResponse,
  ObjectivesResponse,
  JiraDashboardData,
} from "../types/dashboard";
import { getAccessToken } from "@/services/api";

// API base URL - adjust based on your environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Generic fetch wrapper with error handling and authentication
async function fetchApi<T>(endpoint: string): Promise<T> {
  // Get the current in-memory access token
  const token = getAccessToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  // Add authorization header if we have a token
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Add /api prefix to endpoint if it doesn't already have it
  const url = endpoint.startsWith("/api")
    ? `${API_BASE_URL}${endpoint}`
    : `${API_BASE_URL}/api${endpoint}`;

  const response = await fetch(url, {
    headers,
    credentials: "include", // Include cookies
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `API Error ${response.status}: ${errorText || response.statusText}`
    );
  }

  return response.json();
}

// Dashboard API functions
export const dashboardApi = {
  // Get comprehensive dashboard data for an organization
  getDashboard: async (orgId: number): Promise<DashboardResponse> => {
    return fetchApi<DashboardResponse>(`/api/organizations/${orgId}/dashboard`);
  },

  // Get organization metrics
  getMetrics: async (orgId: number): Promise<MetricsResponse> => {
    return fetchApi<MetricsResponse>(`/api/organizations/${orgId}/metrics`);
  },

  // Get AI insights
  getInsights: async (orgId: number): Promise<InsightsResponse> => {
    return fetchApi<InsightsResponse>(`/api/organizations/${orgId}/insights`);
  },

  // Get objectives
  getObjectives: async (orgId: number): Promise<ObjectivesResponse> => {
    return fetchApi<ObjectivesResponse>(
      `/api/organizations/${orgId}/objectives`
    );
  },

  // Get metric trends (for charts)
  getMetricTrends: async (
    orgId: number,
    metricName?: string,
    days?: number
  ): Promise<any> => {
    const params = new URLSearchParams();
    if (metricName) params.append("metric_name", metricName);
    if (days) params.append("days", days.toString());

    return fetchApi<any>(`/api/metrics/trends?${params.toString()}`);
  },

  // Get team performance
  getTeams: async (orgId: number): Promise<any> => {
    return fetchApi<any>(`/api/organizations/${orgId}/teams`);
  },

  // Get recommendation stats
  getRecommendationStats: async (orgId: number): Promise<any> => {
    return fetchApi<any>(`/api/organizations/${orgId}/recommendations/stats`);
  },

  // Jira API functions
  getJiraDashboard: async (): Promise<JiraDashboardData> => {
    return fetchApi<JiraDashboardData>("/api/jira/dashboard");
  },

  getJiraIssues: async (
    limit = 50,
    offset = 0,
    status?: string
  ): Promise<any> => {
    const params = new URLSearchParams();
    params.append("limit", limit.toString());
    params.append("offset", offset.toString());
    if (status) params.append("status", status);

    return fetchApi<any>(`/api/jira/issues?${params.toString()}`);
  },

  getJiraProjects: async (): Promise<any> => {
    return fetchApi<any>("/api/jira/projects");
  },

  // Connector file selection API functions
  getConnectorFiles: async (provider: string): Promise<any> => {
    return fetchApi<any>(`/api/connect/files/${provider}`);
  },

  syncConnector: async (provider: string, fileIds?: string[]): Promise<any> => {
    const token = getAccessToken();

    const response = await fetch(`${API_BASE_URL}/api/connect/sync/${provider}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` })
      },
      credentials: 'include',
      body: JSON.stringify({ file_ids: fileIds })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Sync failed: ${errorText || response.statusText}`);
    }

    return response.json();
  },
};
