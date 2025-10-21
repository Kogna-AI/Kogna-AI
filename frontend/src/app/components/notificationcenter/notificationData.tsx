import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Bell
} from 'lucide-react';

export interface Notification {
  id: string;
  type: 'alert' | 'insight' | 'action' | 'update';
  priority: 'high' | 'medium' | 'low';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  category: 'strategic' | 'operational' | 'team' | 'ai';
  actionRequired?: boolean;
}

export const sampleNotifications: Notification[] = [
  {
    id: '1',
    type: 'alert',
    priority: 'high',
    title: 'Team Capacity Warning',
    message: 'Development team has reached 95% capacity. Consider resource reallocation or timeline adjustment.',
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    read: false,
    category: 'operational',
    actionRequired: true
  },
  {
    id: '2',
    type: 'insight',
    priority: 'medium',
    title: 'Market Opportunity Detected',
    message: 'AI analysis shows 34% increase in demand for sustainable products in your target market.',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    read: false,
    category: 'ai',
    actionRequired: false
  },
  {
    id: '3',
    type: 'update',
    priority: 'medium',
    title: 'Q2 Goals Updated',
    message: 'Strategic objectives have been revised based on market analysis. Review updated targets.',
    timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
    read: true,
    category: 'strategic',
    actionRequired: true
  },
  {
    id: '4',
    type: 'action',
    priority: 'high',
    title: 'Decision Required',
    message: 'Budget reallocation proposal pending approval. Marketing team awaiting confirmation.',
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
    read: false,
    category: 'strategic',
    actionRequired: true
  },
  {
    id: '5',
    type: 'insight',
    priority: 'low',
    title: 'Team Performance Insight',
    message: 'Teams with weekly retrospectives show 18% higher satisfaction scores.',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
    read: true,
    category: 'team',
    actionRequired: false
  }
];

export const getIconForType = (type: Notification['type']) => {
  switch (type) {
    case 'alert': return AlertTriangle;
    case 'insight': return () => null; // rendered elsewhere for Kognii icon
    case 'action': return Clock;
    case 'update': return CheckCircle;
    default: return Bell;
  }
};
