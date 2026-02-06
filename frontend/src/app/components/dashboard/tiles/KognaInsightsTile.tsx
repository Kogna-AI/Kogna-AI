"use client";

import { ArrowRight, Sparkles } from "lucide-react";
import { useState } from "react";
import { Button } from "../../../ui/button";
import { aiInsights } from "../dashboardData";
import InsightDetailsModal from "../InsightDetailsModal";

interface KognaInsightsTileProps {
  onOpenAssistant?: () => void;
}

/* Badge color by type - lighter/semi-transparent */
const typeColors: Record<string, string> = {
  opportunity: "bg-emerald-500/20 text-emerald-700 border border-emerald-200",
  risk: "bg-red-500/20 text-red-700 border border-red-200",
  trend: "bg-blue-500/20 text-blue-700 border border-blue-200",
  recommendation: "bg-purple-500/20 text-purple-700 border border-purple-200",
};

/* Badge color by impact - lighter/semi-transparent */
const impactColors: Record<string, string> = {
  High: "bg-orange-500/20 text-orange-700 border border-orange-200",
  Medium: "bg-amber-500/20 text-amber-700 border border-amber-200",
  Low: "bg-slate-500/20 text-slate-700 border border-slate-200",
};

export function KognaInsightsTile({ onOpenAssistant }: KognaInsightsTileProps) {
  const [selectedInsight, setSelectedInsight] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const insights = aiInsights;

  const handleView = (insight: any) => {
    setSelectedInsight(insight);
    setIsModalOpen(true);
  };

  return (
    <>
      {/* Simplified tile — click header to open Ask Kogna */}
      <div className="rounded-xl border border-border bg-gradient-to-br from-indigo-500/10 via-white to-blue-500/10 h-full flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-5 py-4 border-b border-border/50">
          <h3 className="text-base font-semibold text-foreground">
            Kogna Insights
          </h3>
          <p className="text-xs text-muted-foreground">
            Strategic recommendations and predictions
          </p>
        </div>

        {/* Insights list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gradient-to-br from-purple-50/30 via-transparent to-blue-50/30">
          {insights.map((insight, index) => (
            <button
              key={index}
              type="button"
              onClick={() => handleView(insight)}
              className="w-full text-left group rounded-lg p-3.5 space-y-2 bg-card border border-border hover:border-purple-400 hover:scale-[1.01] transition-all duration-200 cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <span
                  className={`inline-flex items-center rounded px-2 py-0.5 text-[10px] font-semibold ${typeColors[insight.type.toLowerCase()] || "bg-slate-600 text-white"}`}
                >
                  {insight.type}
                </span>
                <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                  <span>{insight.confidence}</span>
                  <span
                    className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-semibold ${impactColors[insight.impact] || "bg-slate-500 text-white"}`}
                  >
                    {insight.impact}
                  </span>
                  <ArrowRight className="w-3 h-3 text-muted-foreground/40 group-hover:text-purple-600 group-hover:translate-x-0.5 transition-all" />
                </div>
              </div>
              <h4 className="text-sm font-medium text-foreground leading-snug">
                {insight.title}
              </h4>
              <p className="text-xs text-muted-foreground line-clamp-2">
                {insight.description}
              </p>
            </button>
          ))}
        </div>

        {/* Footer CTA — open Ask Kogna */}
        <div className="px-4 py-3 border-t border-border/50 bg-white/50">
          <Button
            variant="outline"
            className="w-full gap-2 bg-gradient-to-r from-purple-500/5 to-blue-500/5 hover:from-purple-500/10 hover:to-blue-500/10 border-purple-200/50"
            onClick={onOpenAssistant}
          >
            <Sparkles className="w-4 h-4 text-purple-600" />
            Ask Kogna for deeper analysis
          </Button>
        </div>
      </div>

      {/* Insight detail modal */}
      <InsightDetailsModal
        insight={selectedInsight}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedInsight(null);
        }}
      />
    </>
  );
}
