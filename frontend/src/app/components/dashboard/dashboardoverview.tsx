"use client";


import { StarIcon } from "../../../../public/StarIcon"
import Button from '@mui/material/Button';
import Badge from '@mui/material/Badge';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { blue } from '@mui/material/colors';
import { useState } from "react";
import { Card, CardContent, CardHeader } from '@mui/material';
import LinearProgress, { LinearProgressProps } from '@mui/material/LinearProgress';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../ui/dialog';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Target, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  BarChart3,
  DollarSign,
  Calendar,
  Lightbulb,
  Shield,
  Zap,
  X
} from 'lucide-react';
import { KogniiThinkingIcon } from '../../../../public/KogniiThinkingIcon';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';


const performanceData = [
  { month: 'Jan', value: 65 },
  { month: 'Feb', value: 72 },
  { month: 'Mar', value: 68 },
  { month: 'Apr', value: 85 },
  { month: 'May', value: 90 },
  { month: 'Jun', value: 95 },
];

const strategicMetrics = [
  {
    title: 'Strategic Alignment',
    value: '87%',
    change: '+5%',
    trend: 'up',
    icon: Target,
    color: 'text-green-600'
  },
  {
    title: 'Team Efficiency',
    value: '92%',
    change: '+12%',
    trend: 'up',
    icon: Users,
    color: 'text-blue-600'
  },
  {
    title: 'Decision Velocity',
    value: '3.2 days',
    change: '-1.1 days',
    trend: 'up',
    icon: Clock,
    color: 'text-purple-600'
  },
  {
    title: 'Risk Mitigation',
    value: '95%',
    change: '+8%',
    trend: 'up',
    icon: AlertTriangle,
    color: 'text-orange-600'
  }
];

const aiInsights = [
  {
    id: 'marketing-roi',
    type: 'opportunity',
    title: 'Marketing ROI Optimization',
    description: 'AI suggests reallocating 15% of budget from traditional to digital channels',
    impact: 'High',
    confidence: '94%',
    potentialRevenue: '$2.3M',
    timeframe: '3 months',
    departments: ['Marketing', 'Finance', 'Analytics'],
    detailedAnalysis: {
      currentState: 'Current marketing spend shows 3.2x ROI on digital vs 1.8x on traditional channels',
      recommendation: 'Shift $450K from print advertising, radio, and TV to social media advertising, content marketing, and SEO',
      expectedOutcome: '38% increase in qualified leads, 23% reduction in customer acquisition cost',
      riskFactors: ['Market saturation in digital space', 'Learning curve for new platforms'],
      actionSteps: [
        'Analyze current channel performance data',
        'Develop digital campaign strategy',
        'Phase transition over 90 days',
        'Monitor and adjust based on performance'
      ]
    }
  },
  {
    id: 'team-capacity',
    type: 'risk',
    title: 'Team Capacity Alert',
    description: 'Development team approaching 95% capacity - recommend resource reallocation',
    impact: 'Medium',
    confidence: '87%',
    potentialRevenue: '-$1.8M',
    timeframe: '2 weeks',
    departments: ['Engineering', 'HR', 'Product'],
    detailedAnalysis: {
      currentState: 'Development team working at 95% capacity with 3 critical projects in pipeline',
      recommendation: 'Hire 2 senior developers, redistribute current workload, and implement better project prioritization',
      expectedOutcome: 'Prevent burnout, maintain code quality, ensure on-time delivery',
      riskFactors: ['Burnout leading to resignations', 'Quality degradation', 'Missed deadlines'],
      actionSteps: [
        'Immediate hiring of contract developers',
        'Reassess project priorities with stakeholders',
        'Implement pair programming to knowledge share',
        'Review and optimize development processes'
      ]
    }
  },
  {
    id: 'collaboration',
    type: 'insight',
    title: 'Cross-functional Collaboration',
    description: 'Teams with weekly sync meetings show 23% higher project completion rates',
    impact: 'Medium',
    confidence: '91%',
    potentialRevenue: '$850K',
    timeframe: '6 weeks',
    departments: ['All Departments', 'Operations'],
    detailedAnalysis: {
      currentState: 'Analysis of 47 projects shows correlation between meeting frequency and success rates',
      recommendation: 'Implement structured weekly cross-functional sync meetings for all active projects',
      expectedOutcome: '23% improvement in project completion rates, 15% reduction in rework',
      riskFactors: ['Meeting fatigue', 'Scheduling conflicts', 'Overhead concerns'],
      actionSteps: [
        'Design efficient meeting structure template',
        'Train team leads on facilitation',
        'Implement standardized project tracking',
        'Monitor completion rates and adjust'
      ]
    }
  }
];

// Additional data for detailed views
const marketingROIData = [
  { channel: 'Social Media', current: 420, projected: 650, roi: '4.2x' },
  { channel: 'Search Engine', current: 380, projected: 520, roi: '3.8x' },
  { channel: 'Content Marketing', current: 290, projected: 450, roi: '3.1x' },
  { channel: 'Email Marketing', current: 180, projected: 280, roi: '5.6x' },
  { channel: 'Traditional Media', current: 450, projected: 200, roi: '1.8x' }
];

const capacityData = [
  { name: 'Available', value: 5, color: '#10b981' },
  { name: 'Utilized', value: 95, color: '#f59e0b' }
];

const collaborationData = [
  { metric: 'Project Completion Rate', withMeetings: 87, withoutMeetings: 64 },
  { metric: 'On-time Delivery', withMeetings: 92, withoutMeetings: 74 },
  { metric: 'Quality Score', withMeetings: 88, withoutMeetings: 79 },
  { metric: 'Team Satisfaction', withMeetings: 91, withoutMeetings: 73 }
];

const upcomingActions = [
  { task: 'Q2 Strategy Review', due: 'Tomorrow', priority: 'high', status: 'pending' },
  { task: 'Team Performance Analysis', due: '2 days', priority: 'medium', status: 'in-progress' },
  { task: 'Budget Reallocation Meeting', due: '3 days', priority: 'high', status: 'pending' },
  { task: 'Risk Assessment Update', due: '5 days', priority: 'low', status: 'completed' }
];

interface DashboardOverviewProps {
  onStrategySession: () => void;
  user?: any;
}

function InsightDetailsModal({ insight, isOpen, onClose }: { insight: any; isOpen: boolean; onClose: () => void }) {
  if (!insight) return null;

  const getIcon = () => {
    switch (insight.type) {
      case 'opportunity': return <Lightbulb className="w-5 h-5 text-green-600" />;
      case 'risk': return <Shield className="w-5 h-5 text-red-600" />;
      default: return <KogniiThinkingIcon className="w-5 h-5" />;
    }
  };

  const getChartData = () => {
    switch (insight.id) {
      case 'marketing-roi': return marketingROIData;
      case 'team-capacity': return capacityData;
      case 'collaboration': return collaborationData;
      default: return [];
    }
  };

  const renderChart = () => {
    const data = getChartData();
    
    switch (insight.id) {
      case 'marketing-roi':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
              <XAxis dataKey="channel" />
              <YAxis />
              <Bar dataKey="current" fill="#94a3b8" name="Current Spend ($K)" />
              <Bar dataKey="projected" fill="#3b82f6" name="Projected Spend ($K)" />
            </BarChart>
          </ResponsiveContainer>
        );
        
      case 'team-capacity':
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
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        );
        
      case 'collaboration':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} layout="horizontal">
              <XAxis type="number" />
              <YAxis type="category" dataKey="metric" />
              <Bar dataKey="withMeetings" fill="#10b981" name="With Weekly Meetings" />
              <Bar dataKey="withoutMeetings" fill="#ef4444" name="Without Regular Meetings" />
            </BarChart>
          </ResponsiveContainer>
        );
        
      default:
        return null;
    }
  };
}
const theme = createTheme({
  palette: {
    primary: {
      light: blue[300],
      main: blue[500],
      dark: blue[700],
    },
  },
}); 

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
      {/* Header */}
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

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {strategicMetrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <Card key={metric.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="text-sm font-medium">{metric.title}</div>
                <Icon className={`h-4 w-4 ${metric.color}`} />
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
        })}
      </div>

      {/* Performance Chart & AI Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Trend */}
        <Card>
          <CardHeader>
            <div>Performance Trend</div>
            <p className="text-sm text-muted-foreground">Strategic performance over the last 6 months</p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={performanceData}>
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

        {/* AI Insights */}
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
            {aiInsights.map((insight, index) => (
              <div key={index} className="border rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <Badge 
                    // variant={insight.type === 'risk' ? 'destructive' : 
                    //         insight.type === 'opportunity' ? 'default' : 'secondary'}
                  >
                    {insight.type}
                  </Badge>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{insight.confidence} confidence</span>
                    <Badge 
                    // variant="outline" size="sm"
                    >{insight.impact}</Badge>
                  </div>
                </div>
                <h4 className="font-medium">{insight.title}</h4>
                <p className="text-sm text-muted-foreground">{insight.description}</p>
                <Button 
                //   variant="outline" 
                //   size="sm" 
                  className="w-full"
                  onClick={() => handleViewDetails(insight)}
                >
                  View Details <ArrowRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Action Items & Progress */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upcoming Actions */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div>Action Items</div>
            <p className="text-sm text-muted-foreground">Critical tasks and decisions pending</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {upcomingActions.map((action, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    {action.status === 'completed' ? (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    ) : (
                      <Clock className="w-4 h-4 text-orange-600" />
                    )}
                    <div>
                      <h4 className="font-medium">{action.task}</h4>
                      <p className="text-sm text-muted-foreground">Due {action.due}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge 
                    //   variant={action.priority === 'high' ? 'destructive' : 
                    //           action.priority === 'medium' ? 'default' : 'secondary'}
                    >
                      {action.priority}
                    </Badge>
                    <Badge 
                    //</div>variant="outline"
                    >{action.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Strategic Goals Progress */}
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
              <LinearProgress value={85} />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Market Expansion</span>
                <span>72%</span>
              </div>
              <LinearProgress value={72} />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Team Development</span>
                <span>93%</span>
              </div>
              <LinearProgress value={93} />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Innovation Index</span>
                <span>67%</span>
              </div>
              <LinearProgress value={67} />
            </div>
          </CardContent>
        </Card>
      </div>

      <InsightDetailsModal 
        insight={selectedInsight}
        isOpen={isInsightModalOpen}
        onClose={handleCloseInsightModal}
      />
    </div>
  )
}