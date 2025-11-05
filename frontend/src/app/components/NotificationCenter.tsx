"use client"

import { useState } from 'react';
import { Card, CardContent } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import NotificationHeader from './notificationcenter/NotificationHeader';
import NotificationList from './notificationcenter/NotificationList'; // where I'm currently pulling notification data
import { sampleNotifications, Notification } from './notificationcenter/notificationData';

interface NotificationCenterProps {
  onClose: () => void;
}

export function NotificationCenter({ onClose }: NotificationCenterProps) {
  const [selectedTab, setSelectedTab] = useState('all');
  const [notificationList, setNotificationList] = useState<Notification[]>(sampleNotifications);

  const markAsRead = (id: string) => {
    setNotificationList(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));

    // Example: call backend to mark an item read
    // fetch(`/api/notifications/${id}/read`, { method: 'POST' })
    //   .then(res => res.json())
    //   .catch(err => console.error('Failed to mark read', err));
  };

  const markAllAsRead = () => {
    setNotificationList(prev => prev.map(n => ({ ...n, read: true })));

    // Example: call backend to mark all as read
    // fetch(`/api/notifications/mark-all-read`, { method: 'POST' })
    //   .then(res => res.json())
    //   .catch(err => console.error('Failed to mark all read', err));
  };

  const dismissItem = (id: string) => {
    // remove locally
    setNotificationList(prev => prev.filter(n => n.id !== id));

    // Example: call backend to dismiss
    // fetch(`/api/notifications/${id}/dismiss`, { method: 'DELETE' })
    //   .then(res => res.json())
    //   .catch(err => console.error('Failed to dismiss', err));
  };

  const filteredNotifications = notificationList.filter(notification => {
    if (selectedTab === 'all') return true;
    if (selectedTab === 'unread') return !notification.read;
    if (selectedTab === 'actions') return notification.actionRequired;
    return notification.category === selectedTab;
  });

  const unreadCount = notificationList.filter(n => !n.read).length;
  const actionCount = notificationList.filter(n => n.actionRequired && !n.read).length;

  return (
    <Card className="fixed top-4 right-4 w-96 h-[600px] shadow-lg z-50 flex flex-col overflow-auto">
      <NotificationHeader unreadCount={unreadCount} onMarkAll={markAllAsRead} onClose={onClose} />

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
            {/*
              NotificationList expects three handlers now:
              - onItemClick: called when user opens/marks as read
              - onDismiss: called when user dismisses an item (trash/close)

              Replace local handlers with API calls if you hook up a backend.
              Example: fetch('/api/notifications', { method: 'GET' }) to load,
              and use the commented calls above in markAsRead/markAllAsRead/dismissItem.
            */}
            <NotificationList notifications={filteredNotifications} onItemClick={markAsRead} onDismiss={dismissItem} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}