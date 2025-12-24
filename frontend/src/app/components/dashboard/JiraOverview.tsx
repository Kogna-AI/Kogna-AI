'use client';

import React from 'react';
import { Card, CardContent, CardHeader } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { CheckCircle, Clock, AlertCircle, BarChart3, FolderKanban } from 'lucide-react';
import { useJiraDashboard } from '../../hooks/useDashboard';
import type { JiraProject, JiraIssue } from '../../types/dashboard';

export default function JiraOverview() {
  const { data, isLoading, error } = useJiraDashboard({ enabled: true });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <FolderKanban className="w-5 h-5" />
              <h2 className="text-xl font-semibold">Jira Overview</h2>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-gray-500">Loading Jira data...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FolderKanban className="w-5 h-5" />
            <h2 className="text-xl font-semibold">Jira Overview</h2>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <p className="text-sm text-red-500">Error loading Jira data. Please sync your Jira account.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  const { kpis, projects, recent_issues, issues_by_status, issues_by_priority } = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FolderKanban className="w-6 h-6" />
          <h2 className="text-2xl font-bold">Jira Overview</h2>
        </div>
        <Badge variant="secondary" className="gap-1">
          <BarChart3 className="w-3 h-3" />
          {kpis.projects_count} Projects
        </Badge>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Issues</p>
                <h3 className="text-2xl font-bold">{kpis.total_issues}</h3>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Completed</p>
                <h3 className="text-2xl font-bold text-green-600">{kpis.completed_issues}</h3>
                <p className="text-xs text-green-600">{kpis.completion_rate.toFixed(1)}% complete</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">In Progress</p>
                <h3 className="text-2xl font-bold text-blue-600">{kpis.in_progress_issues}</h3>
              </div>
              <Clock className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">High Priority</p>
                <h3 className="text-2xl font-bold text-orange-600">{kpis.high_priority_count}</h3>
              </div>
              <AlertCircle className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Projects and Issues */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Projects */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Projects</h3>
              <Badge>{projects.length}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {projects.length === 0 ? (
                <p className="text-sm text-muted-foreground">No projects found</p>
              ) : (
                projects.map((project: JiraProject) => (
                  <div key={project.key} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{project.key}</Badge>
                        <p className="font-medium">{project.name}</p>
                      </div>
                      <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <CheckCircle className="w-3 h-3 text-green-600" />
                          {project.completed_issues} done
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-blue-600" />
                          {project.in_progress_issues} in progress
                        </span>
                        <span>{project.todo_issues} todo</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold">{project.issues_count}</p>
                      <p className="text-xs text-muted-foreground">issues</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Issues */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Recent Issues</h3>
              <Badge>{recent_issues.length}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {recent_issues.length === 0 ? (
                <p className="text-sm text-muted-foreground">No recent issues</p>
              ) : (
                recent_issues.map((issue: JiraIssue) => (
                  <div key={issue.key} className="p-3 border rounded-lg hover:bg-gray-50">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline" className="text-xs">{issue.key}</Badge>
                          <Badge className={getStatusColor(issue.status)}>{issue.status}</Badge>
                        </div>
                        <p className="text-sm font-medium line-clamp-2">{issue.summary}</p>
                        <div className="flex gap-2 mt-2 text-xs text-muted-foreground">
                          {issue.assignee && <span>👤 {issue.assignee}</span>}
                          {issue.priority && (
                            <Badge variant="secondary" className={getPriorityColor(issue.priority)}>
                              {issue.priority}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Status & Priority Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Issues by Status */}
        <Card>
          <CardHeader>
            <h3 className="font-semibold">Issues by Status</h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(issues_by_status).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge className={getStatusColor(status)}>{status}</Badge>
                  </div>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Issues by Priority */}
        <Card>
          <CardHeader>
            <h3 className="font-semibold">Issues by Priority</h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(issues_by_priority).map(([priority, count]) => (
                <div key={priority} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge className={getPriorityColor(priority)}>{priority}</Badge>
                  </div>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Helper functions for styling
function getStatusColor(status: string): string {
  const statusLower = status.toLowerCase();
  if (statusLower.includes('done') || statusLower.includes('complete')) {
    return 'bg-green-100 text-green-800';
  }
  if (statusLower.includes('progress') || statusLower.includes('active')) {
    return 'bg-blue-100 text-blue-800';
  }
  if (statusLower.includes('review')) {
    return 'bg-purple-100 text-purple-800';
  }
  return 'bg-gray-100 text-gray-800';
}

function getPriorityColor(priority: string): string {
  const priorityLower = priority.toLowerCase();
  if (priorityLower.includes('highest') || priorityLower.includes('critical')) {
    return 'bg-red-100 text-red-800';
  }
  if (priorityLower.includes('high')) {
    return 'bg-orange-100 text-orange-800';
  }
  if (priorityLower.includes('medium')) {
    return 'bg-yellow-100 text-yellow-800';
  }
  return 'bg-gray-100 text-gray-800';
}
