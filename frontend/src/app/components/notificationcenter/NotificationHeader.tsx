import { Bell, CheckCircle, X } from "lucide-react";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import { CardHeader, CardTitle } from "../../ui/card";

export default function NotificationHeader({
  unreadCount,
  onMarkAll,
  onClose,
}: {
  unreadCount: number;
  onMarkAll: () => void;
  onClose: () => void;
}) {
  return (
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
          <Button variant="ghost" size="sm" onClick={onMarkAll}>
            <CheckCircle className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </CardHeader>
  );
}
