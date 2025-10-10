import React from 'react';
import { Card, CardContent, CardHeader } from '@mui/material';
import Badge from '@mui/material/Badge';
import Button from '@mui/material/Button';
import { ArrowRight } from 'lucide-react';
import { KogniiThinkingIcon } from '../../../../public/KogniiThinkingIcon';

export default function InsightsList({ insights, onView }: { insights: any[]; onView: (insight: any) => void }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>Kognii AI Insights</div>
          <Badge className="gap-1">
            <KogniiThinkingIcon className="w-3 h-3" />
            AI Powered
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">Strategic recommendations and predictions</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {insights.map((insight, index) => (
          <div key={index} className="border rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between">
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
