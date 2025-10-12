"use client";

import Button from '@mui/material/Button';
import { useState } from 'react';
import { StarIcon } from "../../../../public/StarIcon";
import MetricCard from './MetricCard';
import PerformanceTrend from './PerformanceTrend';
import InsightsList from './InsightsList';
import InsightDetailsModal from './InsightDetailsModal';
import ActionItems from './ActionItems';
import StrategicGoals from './StrategicGoals';
import { performanceData, strategicMetrics, aiInsights, upcomingActions } from './dashboardData';

interface DashboardOverviewProps {
  onStrategySession: () => void;
  user?: any;
}

export function DashboardOverview({ onStrategySession, user }: DashboardOverviewProps) {
  const [selectedInsight, setSelectedInsight] = useState<any>(null);
  const [isInsightModalOpen, setIsInsightModalOpen] = useState(false);

  const handleViewDetails = (insight: any) => {
    setSelectedInsight(insight);
    setIsInsightModalOpen(true);
  };

  const handleCloseInsightModal = () => {
    setIsInsightModalOpen(false);
    setSelectedInsight(null);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1>Good morning, {user?.name || 'Allen'}</h1>
          <p className="text-muted-foreground">Here's your strategic overview and AI-powered insights</p>
        </div>
        <Button className="gap-2" onClick={onStrategySession}>
          <StarIcon className="w-4 h-4" />
          AI Strategy Session
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {strategicMetrics.map((metric, idx) => (
          <MetricCard key={idx} metric={metric} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PerformanceTrend data={performanceData} />
        <InsightsList insights={aiInsights} onView={handleViewDetails} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ActionItems actions={upcomingActions} />
        <StrategicGoals />
      </div>

      <InsightDetailsModal insight={selectedInsight} isOpen={isInsightModalOpen} onClose={handleCloseInsightModal} />
    </div>
  );
}