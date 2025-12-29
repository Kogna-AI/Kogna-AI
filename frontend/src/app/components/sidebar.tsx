import {
  LayoutDashboard,
  Users,
  Target,
  Bell,
  Settings,
  Database,
  LogOut,
  Brain,
} from "lucide-react";
// Using Next.js Image component for better optimization
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Separator } from "../ui/seperator";
import { KogniiThinkingIcon } from "../../../public/KogniiThinkingIcon";
import { useUser } from "./auth/UserContext";
import KognaLogo from "../../../public/KognaKLetterLogo.png";

interface SidebarProps {
  activeView: string;
  setActiveView: (view: string) => void;
  onKogniiToggle: () => void;
  onNotificationsToggle: () => void;
}

const getUserDisplayName = (user: any) => {
  if (!user) return "";
  const fullName = [user.first_name, user.second_name].filter(Boolean).join(" ");
  return fullName || user.email || "";
};

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
  const pathname = usePathname();

  const navigationItems: NavItem[] = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "team", label: "Team Overview", icon: Users },
    { id: "strategy", label: "Strategy Hub", icon: Target },
    { id: "connectors", label: "Data Connectors", icon: Database },
    // { id: "insights", label: "Insights", icon: Brain },
  ];

  return (
    <div className="w-64 relative bg-gradient-to-br from-slate-50/95 via-white/95 to-gray-50/95 backdrop-blur-xl border-r border-white/20 shadow-lg flex flex-col">
      {/* Header */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-blue-500/5 to-transparent pointer-events-none"></div>
      <div className="p-6 border-b border-white/20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center overflow-hidden">
            <Image
              src={KognaLogo}
              alt="KognaDash Logo"
              width={20}
              height={20}
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
      <div className="relative p-4 border-b border-white/20">
        <div className="space-y-2">
          <Button
            onClick={onKogniiToggle}
            variant="outline"
            size="sm"
            className="w-full justify-start gap-2 bg-gradient-to-br from-purple-500/10 via-white/60 to-blue-500/10 backdrop-blur-md border-white/10 hover:bg-white/70 hover:shadow-md transition-all duration-300 group"
          >
            <div className="p-1 rounded bg-gradient-to-br from-purple-500/20 to-blue-500/20">
              <KogniiThinkingIcon className="w-4 h-4 text-purple-600" />
            </div>
            <span className="font-medium">Kognii Assistant</span>
            <Badge className="ml-auto text-xs bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-purple-700 border-purple-200/50 backdrop-blur-sm">
              AI
            </Badge>
          </Button>

          <Button
            onClick={onNotificationsToggle}
            variant="outline"
            size="sm"
            className="w-full justify-start gap-2 bg-white/60 backdrop-blur-md border-white/40 hover:bg-white/70 hover:shadow-md transition-all duration-300 group"
          >
            <div className="p-1 rounded bg-gradient-to-br from-orange-500/20 to-red-500/20">
              <Bell className="w-4 h-4 text-orange-600" />
            </div>
            <span className="font-medium">Notifications</span>
            <Badge className="ml-auto text-xs bg-gradient-to-r from-red-500/20 to-rose-500/20 text-red-700 border-red-200/50 backdrop-blur-sm">
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
            const isActive =
              pathname === `/${item.id}` ||
              (pathname === "/" && item.id === "dashboard");
            return (
              <Link key={item.id} href={`/${item.id}`}>
                <Button
                  variant={isActive ? "secondary" : "ghost"}
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
              </Link>
            );
          })}
        </nav>
      </div>

      <Separator className="bg-sidebar-border" />

      {/* Footer */}
      <div className="p-4 space-y-2">
        <Link href="/settings">
          <Button
            variant={pathname === "/settings" ? "secondary" : "ghost"}
            className="w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent"
          >
            <Settings className="w-4 h-4" />
            Settings
          </Button>
        </Link>

        <Button
          onClick={logout}
          variant="ghost"
          className="w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent"
        >
          <LogOut className="w-4 h-4" />
          {getUserDisplayName(user)
            ? `Sign Out (${getUserDisplayName(user)})`
            : "Sign Out"}
        </Button>
      </div>
    </div>
  );
}
