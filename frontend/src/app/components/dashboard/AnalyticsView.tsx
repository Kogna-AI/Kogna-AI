import { Activity, BarChart3, TrendingUp } from "lucide-react";
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "../../ui/card";

const analyticsData = [
  { month: "Jan", performance: 65, efficiency: 70, satisfaction: 75 },
  { month: "Feb", performance: 72, efficiency: 75, satisfaction: 78 },
  { month: "Mar", performance: 68, efficiency: 73, satisfaction: 72 },
  { month: "Apr", performance: 85, efficiency: 82, satisfaction: 85 },
  { month: "May", performance: 90, efficiency: 88, satisfaction: 90 },
  { month: "Jun", performance: 95, efficiency: 92, satisfaction: 95 },
];

export function AnalyticsView() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1>Analytics</h1>
        <p className="text-muted-foreground">
          Deep insights and performance analytics
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Performance Score
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">95%</div>
            <p className="text-xs text-muted-foreground">+8% from last month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Team Efficiency
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">92%</div>
            <p className="text-xs text-muted-foreground">+5% improvement</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Satisfaction</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">95%</div>
            <p className="text-xs text-muted-foreground">All-time high</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Performance Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={analyticsData}>
              <XAxis dataKey="month" />
              <YAxis />
              <Line
                type="monotone"
                dataKey="performance"
                stroke="#3b82f6"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="efficiency"
                stroke="#10b981"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="satisfaction"
                stroke="#f59e0b"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
