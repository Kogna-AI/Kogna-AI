// BE connect data
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
  X,
} from "lucide-react";

export const performanceData = [
  { month: 'Jan', value: 65 },
  { month: 'Feb', value: 72 },
  { month: 'Mar', value: 68 },
  { month: 'Apr', value: 85 },
  { month: 'May', value: 90 },
  { month: 'Jun', value: 95 },
];

export const strategicMetrics = [
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

export const aiInsights = [
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

export const marketingROIData = [
  { channel: 'Social Media', current: 420, projected: 650, roi: '4.2x' },
  { channel: 'Search Engine', current: 380, projected: 520, roi: '3.8x' },
  { channel: 'Content Marketing', current: 290, projected: 450, roi: '3.1x' },
  { channel: 'Email Marketing', current: 180, projected: 280, roi: '5.6x' },
  { channel: 'Traditional Media', current: 450, projected: 200, roi: '1.8x' }
];

export const capacityData = [
  { name: 'Available', value: 5, color: '#10b981' },
  { name: 'Utilized', value: 95, color: '#f59e0b' }
];

export const collaborationData = [
  { metric: 'Project Completion Rate', withMeetings: 87, withoutMeetings: 64 },
  { metric: 'On-time Delivery', withMeetings: 92, withoutMeetings: 74 },
  { metric: 'Quality Score', withMeetings: 88, withoutMeetings: 79 },
  { metric: 'Team Satisfaction', withMeetings: 91, withoutMeetings: 73 }
];

export const upcomingActions = [
  { task: 'Q2 Strategy Review', due: 'Tomorrow', priority: 'high', status: 'pending' },
  { task: 'Team Performance Analysis', due: '2 days', priority: 'medium', status: 'in-progress' },
  { task: 'Budget Reallocation Meeting', due: '3 days', priority: 'high', status: 'pending' },
  { task: 'Risk Assessment Update', due: '5 days', priority: 'low', status: 'completed' }
];
