import React from 'react';
import { Card, CardContent, CardHeader } from '@mui/material';
import LinearProgress from '@mui/material/LinearProgress';

export default function StrategicGoals() {
  return (
    <Card>
      <CardHeader>
        <div>Strategic Goals</div>
        <p className="text-sm text-muted-foreground">Q2 2025 Progress</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Revenue Growth</span>
            <span>85%</span>
          </div>
          <LinearProgress variant="determinate" value={85} />
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Market Expansion</span>
            <span>72%</span>
          </div>
          <LinearProgress variant="determinate" value={72} />
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Team Development</span>
            <span>93%</span>
          </div>
          <LinearProgress variant="determinate" value={93} />
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Innovation Index</span>
            <span>67%</span>
          </div>
          <LinearProgress variant="determinate" value={67} />
        </div>
      </CardContent>
    </Card>
  );
}
