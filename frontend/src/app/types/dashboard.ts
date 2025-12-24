// Dashboard API Types
export interface Metric {
  name: string;
  value: number | string;
  unit?: string;
  change_from_last?: number;
  last_updated: string;
}

export interface Objective {
  id: number;
  title: string;
  progress: number;
  status: 'on-track' | 'at-risk' | 'delayed' | 'completed';
  team_responsible: string;
}

export interface AIInsight {
  id: number | string;
  category: string;
  title: string;
  confidence: number;
  level: 'high' | 'medium' | 'low';
  created_at: string;
  description?: string;
  status?: 'active' | 'dismissed' | 'implemented';
}

export interface OrganizationOverview {
  id: number;
  name: string;
  total_users?: number;
  total_teams?: number;
  active_objectives?: number;
  [key: string]: any; // For additional dashboard fields
}

export interface DashboardData {
  overview: OrganizationOverview;
  recent_metrics: Metric[];
  at_risk_objectives: Objective[];
  active_insights: AIInsight[];
}

export interface DashboardResponse {
  success: boolean;
  data: DashboardData;
}

// Performance data for charts
export interface PerformanceDataPoint {
  month: string;
  value: number;
}

// Metric card data
export interface MetricCardData {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
  icon?: any;
  color?: string;
}

// Metrics API response
export interface MetricsResponse {
  success: boolean;
  data: Metric[];
}

// Insights API response
export interface InsightsResponse {
  success: boolean;
  data: AIInsight[];
}

// Objectives API response
export interface ObjectivesResponse {
  success: boolean;
  data: Objective[];
}

// Jira Types (reusing existing dashboard patterns)
export interface JiraKPIs {
  total_issues: number;
  completed_issues: number;
  in_progress_issues: number;
  todo_issues: number;
  completion_rate: number;
  projects_count: number;
  high_priority_count: number;
  blocked_issues: number;
}

export interface JiraProject {
  key: string;
  name: string;
  issues_count: number;
  completed_issues: number;
  in_progress_issues: number;
  todo_issues: number;
}

export interface JiraIssue {
  key: string;
  summary: string;
  status: string;
  priority?: string;
  assignee?: string;
  created: string;
  updated: string;
}

export interface JiraDashboardData {
  kpis: JiraKPIs;
  projects: JiraProject[];
  recent_issues: JiraIssue[];
  issues_by_status: Record<string, number>;
  issues_by_priority: Record<string, number>;
}
