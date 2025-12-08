import { Card, CardContent, CardHeader } from "@mui/material";
import { Area, AreaChart, ResponsiveContainer, XAxis, YAxis } from "recharts";

export default function PerformanceTrend({ data }: { data: any[] }) {
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
          <AreaChart data={data}>
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
