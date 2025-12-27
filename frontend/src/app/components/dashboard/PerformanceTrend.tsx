import React from "react";
import { Card, CardContent, CardHeader } from "@mui/material";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis } from "recharts";
import { useMetricTrends } from "@/app/hooks/useDashboard";

interface PerformanceTrendProps {
  data?: Array<{ date: string; value: number }>;
  orgId?: number;
  metricName?: string;
  useLiveData?: boolean;
}
export default function PerformanceTrend({
  data,
  orgId,
  metricName = "performance",
  useLiveData = false,
}: PerformanceTrendProps) {
  // Fetch live data if enabled and orgId is provided
  const {
    data: apiData,
    isLoading,
    error,
  } = useMetricTrends(
    orgId || 0,
    metricName,
    180, // Last 180 days (6 months)
    { enabled: useLiveData && !!orgId }
  );

  // Use provided data or fetched data
  const chartData = useLiveData && apiData?.data ? apiData.data : data;

  // Show loading state
  if (useLiveData && isLoading) {
    return (
      <Card>
        <CardHeader>
          <div>Performance Trend</div>
          <p className="text-sm text-muted-foreground">
            Loading performance data...
          </p>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center">
            <p className="text-sm text-gray-500">Loading...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Show error state
  if (useLiveData && error) {
    return (
      <Card>
        <CardHeader>
          <div>Performance Trend</div>
          <p className="text-sm text-red-500">Error loading data</p>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center">
            <p className="text-sm text-red-500">{error.message}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div>Performance Trend</div>
        <p className="text-sm text-muted-foreground">
          Strategic performance over the last 6 months
        </p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <XAxis dataKey="month" />
            <YAxis />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.1}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
