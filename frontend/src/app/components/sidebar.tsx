import {
  LayoutDashboard,
  Users,
  Target,
  Bell,
  Settings,
  Database,
  LogOut,
  Brain,
  Sparkles,
  CreditCard,
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
  const fullName = [user.first_name, user.second_name]
    .filter(Boolean)
    .join(" ");
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
    { id: "pricing", label: "Pricing & Plans", icon: CreditCard },
    // { id: "insights", label: "Insights", icon: Brain },
  ];

  return (
    <div className="fixed left-0 top-0 w-64 h-screen bg-gradient-to-br from-slate-50/95 via-white/95 to-gray-50/95 backdrop-blur-xl border-r border-white/20 shadow-2xl flex flex-col z-40 overflow-hidden">
      {/* Subtle Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-blue-500/5 to-transparent pointer-events-none"></div>
      
      {/* Header */}
      <div className="relative p-6 border-b border-white/20">
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 flex items-center justify-center overflow-hidden transform transition-all duration-300 group-hover:scale-110 group-hover:rotate-6 group-hover:shadow-lg shadow-purple-500/20">
            <Image
              src={KognaLogo}
              alt="KognaDash Logo"
              width={24}
              height={24}
              className="object-contain transition-transform duration-300 group-hover:scale-110"
            />
          </div>
          <div className="transition-all duration-300">
            <h1 className="text-lg font-bold text-sidebar-foreground bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              Kogna
            </h1>
            <p className="text-xs text-sidebar-foreground/60 transition-colors duration-300 group-hover:text-sidebar-foreground/80">
              Strategic Intelligence
            </p>
          </div>
          <Sparkles className="w-4 h-4 ml-auto text-purple-500 opacity-0 group-hover:opacity-100 transition-all duration-300 group-hover:rotate-12" />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="relative p-4 border-b border-white/20">
        <div className="space-y-2">
          <Button
            onClick={onKogniiToggle}
            variant="outline"
            size="sm"
            className="w-full justify-start gap-2 bg-gradient-to-br from-purple-500/10 via-white/60 to-blue-500/10 backdrop-blur-md border-white/10 hover:bg-gradient-to-br hover:from-purple-500/20 hover:to-blue-500/20 hover:shadow-lg hover:shadow-purple-500/20 hover:scale-[1.02] hover:-translate-y-0.5 transition-all duration-300 group relative overflow-hidden"
          >
            {/* Shimmer Effect */}
            <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
            
            <div className="p-1 rounded bg-gradient-to-br from-purple-500/20 to-blue-500/20 group-hover:from-purple-500/30 group-hover:to-blue-500/30 transition-all duration-300">
              <KogniiThinkingIcon className="w-4 h-4 text-purple-600 group-hover:scale-110 transition-transform duration-300" />
            </div>
            <span className="font-medium relative z-10">Kogna Assistant</span>
            <Badge className="ml-auto text-xs bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-purple-700 border-purple-200/50 backdrop-blur-sm group-hover:from-purple-500/30 group-hover:to-blue-500/30 transition-all duration-300 relative z-10">
              AI
            </Badge>
          </Button>

          <Button
            onClick={onNotificationsToggle}
            variant="outline"
            size="sm"
            className="w-full justify-start gap-2 bg-white/60 backdrop-blur-md border-white/40 hover:bg-gradient-to-br hover:from-orange-500/10 hover:to-red-500/10 hover:shadow-lg hover:shadow-orange-500/20 hover:scale-[1.02] hover:-translate-y-0.5 transition-all duration-300 group relative overflow-hidden"
          >
            {/* Shimmer Effect */}
            <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
            
            <div className="p-1 rounded bg-gradient-to-br from-orange-500/20 to-red-500/20 group-hover:from-orange-500/30 group-hover:to-red-500/30 transition-all duration-300">
              <Bell className="w-4 h-4 text-orange-600 group-hover:rotate-12 group-hover:scale-110 transition-transform duration-300" />
            </div>
            <span className="font-medium relative z-10">Notifications</span>
            <Badge className="ml-auto text-xs bg-gradient-to-r from-red-500/20 to-rose-500/20 text-red-700 border-red-200/50 backdrop-blur-sm group-hover:from-red-500/30 group-hover:to-rose-500/30 transition-all duration-300 relative z-10">
              3
            </Badge>
          </Button>
        </div>
      </div>
      {/* Navigation */}
      <div className="flex-1 p-4 overflow-y-auto scrollbar-thin scrollbar-thumb-purple-500/20 scrollbar-track-transparent">
        <nav className="space-y-1.5">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === `/${item.id}` ||
              (pathname === "/" && item.id === "dashboard");
            return (
              <Link 
                key={item.id} 
                href={`/${item.id}`}
                className="block"
              >
                <Button
                  variant={isActive ? "secondary" : "ghost"}
                  className={`
                    w-full justify-start gap-3 text-sidebar-foreground 
                    transition-all duration-300 group relative overflow-hidden
                    ${isActive 
                      ? 'bg-gradient-to-r from-purple-500/10 to-blue-500/10 shadow-md border-l-2 border-purple-500 hover:shadow-lg' 
                      : 'hover:bg-gradient-to-r hover:from-purple-500/5 hover:to-blue-500/5 hover:translate-x-1 hover:shadow-sm'
                    }
                  `}
                >
                  {/* Hover Shimmer */}
                  <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
                  
                  <div className={`
                    p-1.5 rounded-lg transition-all duration-300
                    ${isActive 
                      ? 'bg-gradient-to-br from-purple-500/20 to-blue-500/20 shadow-sm' 
                      : 'bg-transparent group-hover:bg-gradient-to-br group-hover:from-purple-500/10 group-hover:to-blue-500/10'
                    }
                  `}>
                    <Icon className={`
                      w-4 h-4 transition-all duration-300
                      ${isActive 
                        ? 'text-purple-600' 
                        : 'text-sidebar-foreground/70 group-hover:text-purple-600 group-hover:scale-110'
                      }
                    `} />
                  </div>
                  
                  <span className={`
                    font-medium transition-all duration-300 relative z-10
                    ${isActive ? 'text-purple-700' : 'group-hover:text-purple-600'}
                  `}>
                    {item.label}
                  </span>
                  
                  {item.badge && (
                    <Badge variant="secondary" className="ml-auto text-xs relative z-10 transition-all duration-300">
                      {item.badge}
                    </Badge>
                  )}
                  
                  {/* Arrow indicator for active */}
                  {isActive && (
                    <div className="ml-auto w-1.5 h-1.5 rounded-full bg-purple-500 relative z-10"></div>
                  )}
                </Button>
              </Link>
            );
          })}
        </nav>
      </div>

      <Separator className="bg-gradient-to-r from-transparent via-purple-500/20 to-transparent" />

      {/* Footer */}
      <div className="relative p-4 space-y-2">
        <Link href="/settings">
          <Button
            variant={pathname === "/settings" ? "secondary" : "ghost"}
            className={`
              w-full justify-start gap-3 text-sidebar-foreground 
              transition-all duration-300 group relative overflow-hidden
              ${pathname === "/settings"
                ? 'bg-gradient-to-r from-purple-500/10 to-blue-500/10 shadow-md'
                : 'hover:bg-gradient-to-r hover:from-slate-500/5 hover:to-gray-500/5 hover:translate-x-1'
              }
            `}
          >
            {/* Hover Shimmer */}
            <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
            
            <div className={`
              p-1.5 rounded-lg transition-all duration-300
              ${pathname === "/settings"
                ? 'bg-gradient-to-br from-purple-500/20 to-blue-500/20'
                : 'group-hover:bg-slate-500/10'
              }
            `}>
              <Settings className={`
                w-4 h-4 transition-all duration-300
                ${pathname === "/settings"
                  ? 'text-purple-600 rotate-90'
                  : 'text-sidebar-foreground/70 group-hover:text-slate-600 group-hover:rotate-90 group-hover:scale-110'
                }
              `} />
            </div>
            <span className="font-medium relative z-10">Settings</span>
          </Button>
        </Link>

        <Button
          onClick={logout}
          variant="ghost"
          className="w-full justify-start gap-3 text-sidebar-foreground hover:bg-gradient-to-r hover:from-red-500/5 hover:to-rose-500/5 hover:translate-x-1 transition-all duration-300 group relative overflow-hidden"
        >
          {/* Hover Shimmer */}
          <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
          
          <div className="p-1.5 rounded-lg group-hover:bg-red-500/10 transition-all duration-300">
            <LogOut className="w-4 h-4 text-sidebar-foreground/70 group-hover:text-red-600 group-hover:-translate-x-0.5 transition-all duration-300" />
          </div>
          <span className="font-medium text-sm relative z-10 group-hover:text-red-600 transition-colors duration-300">
            {getUserDisplayName(user)
              ? `Sign Out (${getUserDisplayName(user)})`
              : "Sign Out"}
          </span>
        </Button>
        
        {/* Decorative Bottom Border */}
        <div className="absolute bottom-0 left-4 right-4 h-0.5 bg-gradient-to-r from-transparent via-purple-500/30 to-transparent"></div>
      </div>
    </div>
  );
}
