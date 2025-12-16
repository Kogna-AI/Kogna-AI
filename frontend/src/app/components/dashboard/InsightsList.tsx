'use client';

import React from 'react';
import { Card, CardContent, CardHeader } from '../../ui/card';
import {Badge} from '../../ui/badge';
import {Button} from '../../ui/button';
import { ArrowRight } from 'lucide-react';
import { KogniiThinkingIcon } from '../../../../public/KogniiThinkingIcon';
import { useInsights } from '../../hooks/useDashboard';
import type { AIInsight } from '../../types/dashboard';

interface InsightsListProps {
  insights?: any[];
  onView: (insight: any) => void;
  orgId?: number;
  useLiveData?: boolean;
}

export default function InsightsList({
  insights,
  onView,
  orgId,
  useLiveData = false
}: InsightsListProps) {
  // Fetch live data if enabled
  const { data: apiData, isLoading, error } = useInsights(
    orgId || 0,
    { enabled: useLiveData && !!orgId }
  );

  // Use API data or provided data
  const displayInsights = useLiveData && apiData?.data
    ? apiData.data.map((insight: AIInsight) => ({
        id: insight.id,
        type: insight.category,
        title: insight.title,
        description: insight.description || 'No description available',
        confidence: `${insight.confidence}%`,
        impact: insight.level,
        ...insight
      }))
    : insights;

  // Show loading state
  if (useLiveData && isLoading) {
    return (
      <Card className='relative overflow-hidden border-white/20 bg-gradient-to-br from-purple-50/50 via-white/50 to-blue-50/50 backdrop-blur-sm'>
        <CardHeader>
          <div>Kognii AI Insights</div>
          <p className="text-sm text-muted-foreground">Loading insights...</p>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <p className="text-sm text-gray-500">Loading...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Show error state
  if (useLiveData && error) {
    return (
      <Card className='relative overflow-hidden border-white/20 bg-gradient-to-br from-purple-50/50 via-white/50 to-blue-50/50 backdrop-blur-sm'>
        <CardHeader>
          <div>Kognii AI Insights</div>
          <p className="text-sm text-red-500">Error loading insights</p>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <p className="text-sm text-red-500">{error.message}</p>
          </div>
        </CardContent>
      </Card>
    );
  }
  return (
    <Card className='relative overflow-hidden border-white/20 bg-gradient-to-br from-purple-50/50 via-white/50 to-blue-50/50 backdrop-blur-sm'>
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-blue-500/5 pointer-events-none"></div>
      <CardHeader>
        <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500/10 to-blue-500/10 backdrop-blur-sm">
          <div>Kognii AI Insights</div>
          <Badge variant="secondary" className="gap-1 bg-white/50 backdrop-blur-sm border-white/20">
            <KogniiThinkingIcon className="w-3 h-3" />
            AI Powered
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">Strategic recommendations and predictions</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {insights.map((insight, index) => (
          <div key={index} 
              className="group relative overflow-hidden rounded-xl p-4 space-y-3 bg-white/60 backdrop-blur-md border border-white/40 hover:bg-white/70 hover:shadow-lg hover:scale-[1.02] transition-all duration-300">
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>

            <div className="relative flex items-center justify-between">
              <Badge>
                {insight.type}
              </Badge>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>{insight.confidence} confidence</span>
                <Badge>{insight.impact}</Badge>
              </div>
            </div>
            <h4 className="font-medium">{insight.title}</h4>
            <p className="text-sm text-muted-foreground">{insight.description}</p>
            <Button className="w-full" onClick={() => onView(insight)}>
              View Details <ArrowRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
