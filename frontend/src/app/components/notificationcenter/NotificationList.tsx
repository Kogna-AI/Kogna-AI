import { Bell } from "lucide-react";
import { ScrollArea } from "../../ui/scroll-area";
import NotificationItem from "./NotificationItem";
import type { Notification } from "./notificationData";

export default function NotificationList({
  notifications,
  onItemClick,
  onDismiss,
}: {
  notifications: Notification[];
  onItemClick: (id: string) => void;
  onDismiss: (id: string) => void;
}) {
  return (
    <ScrollArea className="h-full px-6 overflow-scroll">
      <div className="space-y-3 pb-4">
        {notifications.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No notifications</p>
          </div>
        ) : (
          notifications.map((n) => (
            <NotificationItem
              key={n.id}
              notification={n}
              onClick={onItemClick}
              onDismiss={onDismiss}
            />
          ))
        )}
      </div>
    </ScrollArea>
  );
}
