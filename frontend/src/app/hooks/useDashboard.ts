import { useQuery, useMutation, useQueryClient, type UseQueryResult } from '@tanstack/react-query';
import { dashboardApi } from '../services/dashboardApi';
import type {
  DashboardResponse,
  MetricsResponse,
  InsightsResponse,
  ObjectivesResponse,
  JiraDashboardData,
} from '../types/dashboard';

// Hook for getting full dashboard data
export function useDashboard(
  orgId: number,
  options?: { enabled?: boolean }
): UseQueryResult<DashboardResponse, Error> {
  return useQuery({
    queryKey: ['dashboard', orgId],
    queryFn: () => dashboardApi.getDashboard(orgId),
    staleTime: 30000, // Data stays fresh for 30 seconds
    refetchInterval: 60000, // Auto-refetch every 60 seconds
    ...options,
  });
}

// Hook for getting metrics
export function useMetrics(
  orgId: number,
  options?: { enabled?: boolean }
): UseQueryResult<MetricsResponse, Error> {
  return useQuery({
    queryKey: ['metrics', orgId],
    queryFn: () => dashboardApi.getMetrics(orgId),
    staleTime: 30000,
    refetchInterval: 60000,
    ...options,
  });
}

// Hook for getting AI insights
export function useInsights(
  orgId: number,
  options?: { enabled?: boolean }
): UseQueryResult<InsightsResponse, Error> {
  return useQuery({
    queryKey: ['insights', orgId],
    queryFn: () => dashboardApi.getInsights(orgId),
    staleTime: 30000,
    refetchInterval: 60000,
    ...options,
  });
}

// Hook for getting objectives
export function useObjectives(
  orgId: number,
  options?: { enabled?: boolean }
): UseQueryResult<ObjectivesResponse, Error> {
  return useQuery({
    queryKey: ['objectives', orgId],
    queryFn: () => dashboardApi.getObjectives(orgId),
    staleTime: 30000,
    refetchInterval: 60000,
    ...options,
  });
}

// Hook for getting metric trends (for charts)
export function useMetricTrends(
  orgId: number,
  metricName?: string,
  days?: number,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['metric-trends', orgId, metricName, days],
    queryFn: () => dashboardApi.getMetricTrends(orgId, metricName, days),
    staleTime: 60000, // Trends can be cached longer
    ...options,
  });
}

// Hook for getting team performance
export function useTeams(orgId: number, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['teams', orgId],
    queryFn: () => dashboardApi.getTeams(orgId),
    staleTime: 60000,
    ...options,
  });
}

// Hook for getting recommendation stats
export function useRecommendationStats(
  orgId: number,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['recommendation-stats', orgId],
    queryFn: () => dashboardApi.getRecommendationStats(orgId),
    staleTime: 60000,
    ...options,
  });
}

// Jira Hooks
export function useJiraDashboard(
  options?: { enabled?: boolean }
): UseQueryResult<JiraDashboardData, Error> {
  return useQuery({
    queryKey: ['jira-dashboard'],
    queryFn: () => dashboardApi.getJiraDashboard(),
    staleTime: 30000,
    refetchInterval: 60000,
    ...options,
  });
}

export function useJiraIssues(
  limit = 50,
  offset = 0,
  status?: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['jira-issues', limit, offset, status],
    queryFn: () => dashboardApi.getJiraIssues(limit, offset, status),
    staleTime: 30000,
    ...options,
  });
}

export function useJiraProjects(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['jira-projects'],
    queryFn: () => dashboardApi.getJiraProjects(),
    staleTime: 60000,
    ...options,
  });
}

// Connector file selection hooks
export function useConnectorFiles(
  provider: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['connector-files', provider],
    queryFn: () => dashboardApi.getConnectorFiles(provider),
    staleTime: 60000, // Cache for 1 minute
    enabled: options?.enabled ?? false, // Only fetch when explicitly enabled
    ...options,
  });
}

export function useSyncConnector() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ provider, fileIds }: { provider: string; fileIds?: string[] }) =>
      dashboardApi.syncConnector(provider, fileIds),
    onSuccess: () => {
      // Invalidate connection status to refresh UI
      queryClient.invalidateQueries({ queryKey: ['connection-status'] });
    },
  });
}

/**
 * Hook to fetch selected file IDs for a connector
 * @param provider - The connector provider (e.g., 'google', 'jira')
 * @param options - Query options including enabled flag
 */
export function useSelectedFiles(
  provider: string | null | undefined,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['selected-files', provider],
    queryFn: () => {
      if (!provider) throw new Error('Provider is required');
      return dashboardApi.getSelectedFiles(provider);
    },
    enabled: options?.enabled ?? false,
    staleTime: 30000, // Cache for 30 seconds
    refetchOnWindowFocus: false,
  });
}
