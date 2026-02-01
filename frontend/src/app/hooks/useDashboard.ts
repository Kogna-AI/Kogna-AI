import { useQuery, type UseQueryResult } from '@tanstack/react-query';
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

// ==================== TEAM OVERVIEW HOOKS ====================

// Import API service for authenticated requests
import api from '@/services/api';

/**
 * Hook for fetching all visible users (team members)
 * Used in TeamOverview to display team members list
 * Uses api.listVisibleUsers() with proper authentication
 */
export function useVisibleUsers(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['visible-users'],
    queryFn: async () => {
      const response = await api.listVisibleUsers();
      const data = (response as any)?.data || response || [];
      return data;
    },
    staleTime: 30000, // 30 seconds - team data changes relatively frequently
    refetchInterval: 120000, // Auto-refetch every 2 minutes
    ...options,
  });
}

/**
 * Hook for fetching team hierarchy
 * Used in TeamOverview to display organizational structure
 * Uses api.teamHierarchy() with proper authentication
 */
export function useTeamHierarchy(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['team-hierarchy'],
    queryFn: async () => {
      const response = await api.teamHierarchy();
      const data = (response as any).data || response || null;
      return data;
    },
    staleTime: 60000, // 60 seconds - hierarchy changes less frequently
    refetchInterval: 180000, // Auto-refetch every 3 minutes
    ...options,
  });
}

/**
 * Hook for fetching a user's primary team
 * Used in TeamOverview to display team header
 * Uses api.getUserTeam() with proper authentication
 */
export function useUserTeam(userId: string | undefined, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['user-team', userId],
    queryFn: async () => {
      if (!userId) return null;
      
      try {
        const response = await api.getUserTeam(userId);
        const data = (response as any)?.data || response || null;
        return data;
      } catch (error) {
        // User might not belong to a team (e.g., founder/CEO) - this is acceptable
        console.log('User team not found:', error);
        return null;
      }
    },
    staleTime: 60000, // 60 seconds
    enabled: !!userId && (options?.enabled ?? true),
    ...options,
  });
}
