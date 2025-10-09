import { 
  Crown, 
  Target, 
  CheckCircle, 
  BarChart3, 
  Calendar, 
  FileSpreadsheet, 
  MessageSquare,
  Database
} from 'lucide-react';
import { Connector, Category } from './types';

export const syncModes = [
  {
    id: 'one-way',
    name: 'One-way Sync',
    description: 'Data flows from external source to KognaDash only',
    icon: '→',
    features: ['Import data', 'View updates', 'Basic reporting']
  },
  {
    id: 'two-way',
    name: 'Two-way Sync',
    description: 'Bidirectional data flow - updates sync both ways',
    icon: '↔',
    features: ['Import & export data', 'Real-time updates', 'Collaborative editing', 'Advanced reporting'],
    isPremium: true
  }
];

export const connectors: Connector[] = [
  {
    id: 'kognacore',
    name: 'KognaCore WBS',
    description: 'Our native Work Breakdown Structure system with deepest AI insights and real-time optimization',
    icon: <Crown className="w-6 h-6 text-amber-500" />,
    status: 'premium',
    category: 'project',
    features: ['AI-Powered Insights', 'Real-time Optimization', 'Predictive Analytics', 'Advanced Reporting', 'Team Workload Balancing'],
    setupTime: '5 minutes',
    dataSync: 'Real-time',
    isPremium: true,
    isRecommended: true
  },
  {
    id: 'jira',
    name: 'Jira',
    description: 'Connect with Atlassian Jira for issue tracking and agile project management',
    icon: <Target className="w-6 h-6 text-blue-600" />,
    status: 'available',
    category: 'project',
    features: ['Issue Tracking', 'Sprint Planning', 'Backlog Management', 'Custom Workflows'],
    setupTime: '10 minutes',
    dataSync: 'Every 15 minutes'
  },
  {
    id: 'asana',
    name: 'Asana',
    description: 'Sync tasks, projects, and team collaboration from Asana',
    icon: <CheckCircle className="w-6 h-6 text-red-500" />,
    status: 'available',
    category: 'project',
    features: ['Task Management', 'Project Timeline', 'Team Collaboration', 'Goal Tracking'],
    setupTime: '8 minutes',
    dataSync: 'Every 20 minutes'
  },
  {
    id: 'smartsheet',
    name: 'Smartsheet',
    description: 'Import project data and work management from Smartsheet',
    icon: <BarChart3 className="w-6 h-6 text-blue-700" />,
    status: 'available',
    category: 'project',
    features: ['Project Planning', 'Resource Management', 'Gantt Charts', 'Automation'],
    setupTime: '12 minutes',
    dataSync: 'Every 30 minutes'
  },
  {
    id: 'msproject',
    name: 'Microsoft Project',
    description: 'Enterprise project management integration with Microsoft Project',
    icon: <Calendar className="w-6 h-6 text-green-600" />,
    status: 'available',
    category: 'project',
    features: ['Project Scheduling', 'Resource Planning', 'Portfolio Management', 'Advanced Analytics'],
    setupTime: '15 minutes',
    dataSync: 'Every hour'
  },
  {
    id: 'sheets',
    name: 'Google Sheets',
    description: 'Connect spreadsheets and data from Google Sheets',
    icon: <FileSpreadsheet className="w-6 h-6 text-green-500" />,
    status: 'connected',
    category: 'storage',
    features: ['Data Import', 'Real-time Collaboration', 'Formula Support', 'Chart Integration'],
    setupTime: '5 minutes',
    dataSync: 'Every 10 minutes'
  },
  {
    id: 'excel',
    name: 'Microsoft Excel',
    description: 'Import and sync data from Microsoft Excel files',
    icon: <FileSpreadsheet className="w-6 h-6 text-green-700" />,
    status: 'available',
    category: 'storage',
    features: ['Data Import', 'File Sync', 'Formula Preservation', 'Chart Migration'],
    setupTime: '8 minutes',
    dataSync: 'Manual/Scheduled'
  },
  {
    id: 'teams',
    name: 'Microsoft Teams',
    description: 'Integrate team communication and meeting data from Teams',
    icon: <MessageSquare className="w-6 h-6 text-purple-600" />,
    status: 'available',
    category: 'communication',
    features: ['Meeting Integration', 'Chat History', 'File Sharing', 'Team Insights'],
    setupTime: '10 minutes',
    dataSync: 'Every 30 minutes'
  }
];

export const categories: Category[] = [
  { id: 'all', name: 'All Integrations', icon: <Database className="w-4 h-4" /> },
  { id: 'project', name: 'Project Management', icon: <Target className="w-4 h-4" /> },
  { id: 'communication', name: 'Communication', icon: <MessageSquare className="w-4 h-4" /> },
  { id: 'storage', name: 'Data & Storage', icon: <FileSpreadsheet className="w-4 h-4" /> },
  { id: 'analytics', name: 'Analytics', icon: <BarChart3 className="w-4 h-4" /> }
];