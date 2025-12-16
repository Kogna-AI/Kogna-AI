import { Lightbulb, Shield } from "lucide-react";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";
import { KogniiThinkingIcon } from "../../../../public/KogniiThinkingIcon";
import { Badge } from "../../ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../../ui/dialog";
import { Tabs } from "../../ui/tabs";
import {
  capacityData,
  collaborationData,
  marketingROIData,
} from "./dashboardData";
export default function InsightDetailsModal({
  insight,
  isOpen,
  onClose,
}: {
  insight: any;
  isOpen: boolean;
  onClose: () => void;
}) {
  if (!insight) return null;

  const getIcon = () => {
    switch (insight.type) {
      case "opportunity":
        return <Lightbulb className="w-5 h-5 text-green-600" />;
      case "risk":
        return <Shield className="w-5 h-5 text-red-600" />;
      default:
        return <KogniiThinkingIcon className="w-5 h-5" />;
    }
  };

  const getChartData = () => {
    switch (insight.id) {
      case "marketing-roi":
        return marketingROIData;
      case "team-capacity":
        return capacityData;
      case "collaboration":
        return collaborationData;
      default:
        return [];
    }
  };

  const renderChart = () => {
    const data = getChartData();
    switch (insight.id) {
      case "marketing-roi":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
              <XAxis dataKey="channel" />
              <YAxis />
              <Bar dataKey="current" fill="#94a3b8" name="Current Spend ($K)" />
              <Bar
                dataKey="projected"
                fill="#3b82f6"
                name="Projected Spend ($K)"
              />
            </BarChart>
          </ResponsiveContainer>
        );
      case "team-capacity":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={120}
                dataKey="value"
              >
                {data.map((_entry: any, index: number) => (
                  <Cell key={`cell-${index}`} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        );
      case "collaboration":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} layout="horizontal">
              <XAxis type="number" />
              <YAxis type="category" dataKey="metric" />
              <Bar
                dataKey="withMeetings"
                fill="#10b981"
                name="With Weekly Meetings"
              />
              <Bar
                dataKey="withoutMeetings"
                fill="#ef4444"
                name="Without Regular Meetings"
              />
            </BarChart>
          </ResponsiveContainer>
        );
      default:
        return null;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{insight.title}</DialogTitle>
          <DialogDescription className="flex items-center gap-4 mt-2">
            <Badge
              variant={
                insight.type === "risk"
                  ? "destructive"
                  : insight.type === "opportunity"
                    ? "default"
                    : "secondary"
              }
            />
            <span className="text-sm">{insight.confidence} confidence</span>
            <Badge variant="outline">{insight.impact} impact</Badge>
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="overview" className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              {getIcon()}
              <span className="text-sm text-muted-foreground">
                {insight.description}
              </span>
            </div>
            {renderChart()}
            <div>
              <h5 className="font-medium">Recommendation</h5>
              <p className="text-sm text-muted-foreground">
                {insight.detailedAnalysis?.recommendation}
              </p>
            </div>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
