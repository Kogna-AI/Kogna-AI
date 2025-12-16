'use client';

import { Card, CardContent, CardHeader } from '../../ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';
import React from 'react';
import type { Metric } from '../../types/dashboard';

interface MetricCardProps {
  metric?: any; // For backwards compatibility with mock data
  apiMetric?: Metric; // For API data
  title?: string;
  icon?: any;
  color?: string;
}

export default function MetricCard({
  metric,
  apiMetric,
  title,
  icon,
  color
}: MetricCardProps) {
  // Use API data if available, otherwise use mock data
  const displayData = apiMetric ? {
    title: title || apiMetric.name,
    value: `${apiMetric.value}${apiMetric.unit || ''}`,
    change: apiMetric.change_from_last
      ? `${apiMetric.change_from_last > 0 ? '+' : ''}${apiMetric.change_from_last}%`
      : 'N/A',
    trend: apiMetric.change_from_last && apiMetric.change_from_last > 0 ? 'up' : 'down',
    icon: icon,
    color: color
  } : metric;

  const Icon = displayData?.icon;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="text-sm black font-medium">{displayData?.title}</div>
        {Icon ? <Icon className={`h-4 w-4 ${displayData?.color}`} /> : null}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{displayData?.value}</div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          {displayData?.trend === 'up' ? (
            <TrendingUp className="h-3 w-3 text-green-600" />
          ) : (
            <TrendingDown className="h-3 w-3 text-red-600" />
          )}
          <span className={displayData?.trend === 'up' ? 'text-green-600' : 'text-red-600'}>
            {displayData?.change}
          </span>
          <span>from last month</span>
        </div>
      </CardContent>
    </Card>
  );
}
