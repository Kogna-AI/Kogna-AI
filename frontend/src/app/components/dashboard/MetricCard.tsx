import { Card, CardContent, CardHeader } from '../../ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';
import React from 'react';

export default function MetricCard({ metric }: { metric: any }) {
  const Icon = metric.icon; //this is totally not picking up anything :C
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="text-sm black font-medium">{metric.title}</div>
        {Icon ? <Icon className={`h-4 w-4 ${metric.color}`} /> : null}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{metric.value}</div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          {metric.trend === 'up' ? (
            <TrendingUp className="h-3 w-3 text-green-600" />
          ) : (
            <TrendingDown className="h-3 w-3 text-red-600" />
          )}
          <span className={metric.trend === 'up' ? 'text-green-600' : 'text-red-600'}>
            {metric.change}
          </span>
          <span>from last month</span>
        </div>
      </CardContent>
    </Card>
  );
}
