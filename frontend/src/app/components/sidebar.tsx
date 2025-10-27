import {
  LayoutDashboard,
  Users,
  Calendar,
  Target,
  TrendingUp,
  MessageSquare,
  Bell,
  Settings,
  Database,
  LogOut,
  Brain,
} from "lucide-react";
// Using Next.js Image component for better optimization
import Image from "next/image";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Separator } from "../ui/seperator";
import { KogniiThinkingIcon } from "../../../public/KogniiThinkingIcon";
import { useUser } from "./auth/UserContext";

interface SidebarProps {
  activeView: string;
  setActiveView: (view: string) => void;
  onKogniiToggle: () => void;
  onNotificationsToggle: () => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: any;
  badge?: string | number;
}

export function Sidebar({
  activeView,
  setActiveView,
  onKogniiToggle,
  onNotificationsToggle,
}: SidebarProps) {
  const { user, logout } = useUser();
  const navigationItems: NavItem[] = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "team", label: "Team Overview", icon: Users },
    { id: "strategy", label: "Strategy Hub", icon: Target },
    { id: "connectors", label: "Data Connectors", icon: Database },
    { id: "meetings", label: "Meetings", icon: Calendar },
    { id: "analytics", label: "Analytics", icon: TrendingUp },
    { id: "feedback", label: "Feedback", icon: MessageSquare },
    { id: "insights", label: "Insights", icon: Brain },
  ];

  return (
    <div className="w-64 relative bg-gradient-to-br from-slate-50/95 via-white/95 to-gray-50/95 backdrop-blur-xl border-r border-white/20 shadow-lg flex flex-col">
      {/* Header */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-blue-500/5 to-transparent pointer-events-none"></div>
      <div className="p-6 border-b border-white/20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center overflow-hidden">
            <Image
              src="/logoImage.svg"
              alt="KognaDash Logo"
              width={32}
              height={32}
              className="object-contain"
            />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-sidebar-foreground">
              KognaDash
            </h1>
            <p className="text-xs text-sidebar-foreground/60">
              Strategic Intelligence
            </p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-4 border-b border-sidebar-border">
        <div className="space-y-2">
          <Button
            onClick={onKogniiToggle}
            variant="outline"
            size="sm"
            className="w-full justify-start gap-2 text-sidebar-foreground border-sidebar-border hover:bg-sidebar-accent"
          >
            <KogniiThinkingIcon className="w-4 h-4" />
            Kognii Assistant
            <Badge variant="secondary" className="ml-auto text-xs">
              AI
            </Badge>
          </Button>

          <Button
            onClick={onNotificationsToggle}
            variant="outline"
            size="sm"
            className="w-full justify-start gap-2 text-sidebar-foreground border-sidebar-border hover:bg-sidebar-accent"
          >
            <Bell className="w-4 h-4" />
            Notifications
            <Badge variant="destructive" className="ml-auto text-xs">
              3
            </Badge>
          </Button>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 p-4">
        <nav className="space-y-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            return (
              <Button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                variant={activeView === item.id ? "secondary" : "ghost"}
                className="w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent"
              >
                <Icon className="w-4 h-4" />
                {item.label}
                {item.badge && (
                  <Badge variant="secondary" className="ml-auto text-xs">
                    {item.badge}
                  </Badge>
                )}
              </Button>
            );
          })}
        </nav>
      </div>

      <Separator className="bg-sidebar-border" />

      {/* Footer */}
      <div className="p-4 space-y-2">
        <Button
          onClick={() => setActiveView("settings")}
          variant="ghost"
          className="w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent"
        >
          <Settings className="w-4 h-4" />
          Settings
        </Button>

        <Button
          onClick={logout}
          variant="ghost"
          className="w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent"
        >
          <LogOut className="w-4 h-4" />
          Sign Out ({user?.name})
        </Button>
      </div>
    </div>
  );
}
