"use client"

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  X, 
  Bell, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  TrendingUp,
  Users,
  Target,
  Filter
} from 'lucide-react';
import { KogniiThinkingIcon } from '../../../public/KogniiThinkingIcon';

interface NotificationCenterProps {
  onClose: () => void;
}

interface Notification {
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

const notifications: Notification[] = [
  {
    id: '1',
    type: 'alert',
    priority: 'high',
    title: 'Team Capacity Warning',
    message: 'Development team has reached 95% capacity. Consider resource reallocation or timeline adjustment.',
    timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 min ago
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
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
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
    timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4 hours ago
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
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6 hours ago
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
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
    read: true,
    category: 'team',
    actionRequired: false
  }
];

export function NotificationCenter({ onClose }: NotificationCenterProps) {
  const [selectedTab, setSelectedTab] = useState('all');
  const [notificationList, setNotificationList] = useState(notifications);

  const getIcon = (type: string) => {
    switch (type) {
      case 'alert':
        return AlertTriangle;
      case 'insight':
        return () => <KogniiThinkingIcon className="w-3 h-3" />;
      case 'action':
        return Clock;
      case 'update':
        return CheckCircle;
      default:
        return Bell;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950';
      case 'medium':
        return 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950';
      default:
        return 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950';
    }
  };

  const markAsRead = (id: string) => {
    setNotificationList(prev =>
      prev.map(notification =>
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
  };

  const markAllAsRead = () => {
    setNotificationList(prev =>
      prev.map(notification => ({ ...notification, read: true }))
    );
  };

  const filteredNotifications = notificationList.filter(notification => {
    if (selectedTab === 'all') return true;
    if (selectedTab === 'unread') return !notification.read;
    if (selectedTab === 'actions') return notification.actionRequired;
    return notification.category === selectedTab;
  });

  const unreadCount = notificationList.filter(n => !n.read).length;
  const actionCount = notificationList.filter(n => n.actionRequired && !n.read).length;

  const formatTimestamp = (timestamp: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - timestamp.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  return (
    <Card className="fixed top-4 right-4 w-96 h-[600px] shadow-lg z-50 flex flex-col">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            <CardTitle>Notifications</CardTitle>
            {unreadCount > 0 && (
              <Badge variant="destructive" className="text-xs">
                {unreadCount}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={markAllAsRead}>
              <CheckCircle className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="flex-1 flex flex-col">
          <div className="px-6 pb-4">
            <TabsList className="grid w-full grid-cols-4 text-xs">
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="unread" className="relative">
                Unread
                {unreadCount > 0 && (
                  <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full" />
                )}
              </TabsTrigger>
              <TabsTrigger value="actions" className="relative">
                Actions
                {actionCount > 0 && (
                  <div className="absolute -top-1 -right-1 w-2 h-2 bg-orange-500 rounded-full" />
                )}
              </TabsTrigger>
              <TabsTrigger value="ai">AI</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value={selectedTab} className="flex-1 mt-0">
            <ScrollArea className="h-full px-6">
              <div className="space-y-3 pb-4">
                {filteredNotifications.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No notifications</p>
                  </div>
                ) : (
                  filteredNotifications.map((notification) => {
                    const Icon = getIcon(notification.type);
                    return (
                      <div
                        key={notification.id}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors hover:bg-muted/50 ${
                          !notification.read ? getPriorityColor(notification.priority) : 'border-border'
                        }`}
                        onClick={() => markAsRead(notification.id)}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`p-1 rounded ${
                            notification.priority === 'high' ? 'bg-red-100 text-red-600' :
                            notification.priority === 'medium' ? 'bg-yellow-100 text-yellow-600' :
                            'bg-blue-100 text-blue-600'
                          }`}>
                            <Icon className="w-3 h-3" />
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className={`text-sm font-medium ${!notification.read ? 'font-semibold' : ''}`}>
                                {notification.title}
                              </h4>
                              {!notification.read && (
                                <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
                              )}
                            </div>
                            
                            <p className="text-xs text-muted-foreground mb-2">
                              {notification.message}
                            </p>
                            
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-muted-foreground">
                                {formatTimestamp(notification.timestamp)}
                              </span>
                              
                              <div className="flex items-center gap-1">
                                <Badge variant="outline" className="text-xs">
                                  {notification.category}
                                </Badge>
                                {notification.actionRequired && (
                                  <Badge variant="secondary" className="text-xs">
                                    Action Required
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}