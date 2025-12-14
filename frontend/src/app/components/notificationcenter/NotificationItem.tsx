import { X } from "lucide-react";
import { KogniiThinkingIcon } from "../../../../public/KogniiThinkingIcon";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import { getIconForType, type Notification } from "./notificationData";

export default function NotificationItem({
  notification,
  onClick,
  onDismiss,
}: {
  notification: Notification;
  onClick: (id: string) => void;
  onDismiss: (id: string) => void;
}) {
  const Icon = getIconForType(notification.type);

  return (
    <div
      key={notification.id}
      className={`p-3 rounded-lg border cursor-pointer transition-colors hover:bg-muted/50 ${
        !notification.read
          ? notification.priority === "high"
            ? "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950"
            : notification.priority === "medium"
              ? "border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950"
              : "border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950"
          : "border-border"
      }`}
      onClick={() => onClick(notification.id)}
    >
      <div className="flex items-start gap-3">
        <div
          className={`p-1 rounded ${
            notification.priority === "high"
              ? "bg-red-100 text-red-600"
              : notification.priority === "medium"
                ? "bg-yellow-100 text-yellow-600"
                : "bg-blue-100 text-blue-600"
          }`}
        >
          {notification.type === "insight" ? (
            <KogniiThinkingIcon className="w-3 h-3" />
          ) : (
            <Icon className="w-3 h-3" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4
              className={`text-sm font-medium ${!notification.read ? "font-semibold" : ""}`}
            >
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
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => {
                  e.stopPropagation();
                  onDismiss(notification.id);
                }}
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function formatTimestamp(timestamp: Date) {
  const now = new Date();
  const diffMs = now.getTime() - timestamp.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}
