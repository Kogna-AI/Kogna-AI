"use client";

import { useState } from "react";
import { StarIcon } from "../../../../public/StarIcon";
import { Button } from "../../ui/button";
import ActionItems from "./ActionItems";
import {
  aiInsights,
  performanceData,
  strategicMetrics,
  upcomingActions,
} from "./dashboardData";
import InsightDetailsModal from "./InsightDetailsModal";
import InsightsList from "./InsightsList";
import MetricCard from "./MetricCard";
import PerformanceTrend from "./PerformanceTrend";
import StrategicGoals from "./StrategicGoals";
import { useAuthUser } from "@/hooks/useAuthUser";
interface DashboardOverviewProps {
  onStrategySession: () => void;
  user?: any;
}

export function DashboardOverview({
  onStrategySession,
  user,
}: DashboardOverviewProps) {
  const [selectedInsight, setSelectedInsight] = useState<any>(null);
  const [isInsightModalOpen, setIsInsightModalOpen] = useState(false);

  const handleViewDetails = (insight: any) => {
    setSelectedInsight(insight);
    setIsInsightModalOpen(true);
  };

  const trendData = performanceData.map((item) => ({
    date: item.month,
    value: item.value,
  }));
  const handleCloseInsightModal = () => {
    setIsInsightModalOpen(false);
    setSelectedInsight(null);
  };

  const { fullName } = useAuthUser();

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1>Good morning, {fullName}</h1>
          <p className="text-muted-foreground">
            Here's your strategic overview and AI-powered insights
          </p>
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
        <PerformanceTrend data={trendData} />
        <InsightsList insights={aiInsights} onView={handleViewDetails} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ActionItems actions={upcomingActions} />
        <StrategicGoals />
      </div>

      <InsightDetailsModal
        insight={selectedInsight}
        isOpen={isInsightModalOpen}
        onClose={handleCloseInsightModal}
      />
    </div>
  );
}
