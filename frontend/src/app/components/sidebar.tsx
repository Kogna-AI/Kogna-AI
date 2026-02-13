import {
  LayoutDashboard,
  Users,
  Target,
  Database,
  HardDrive,
  Sparkles,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import KognaLogo from "../../../public/KognaKLetterLogo.png";

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
  const pathname = usePathname();

  const navigationItems: NavItem[] = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "team", label: "Team Overview", icon: Users },
    { id: "strategy", label: "Strategy Hub", icon: Target },
    { id: "drive", label: "Data Drive", icon: HardDrive },
    { id: "connectors", label: "Data Connectors", icon: Database },
  ];

  return (
    <div className="fixed left-0 top-0 w-64 h-screen bg-gradient-to-br from-slate-50/95 via-white/95 to-gray-50/95 backdrop-blur-xl border-r border-border flex flex-col z-40 overflow-hidden">
      {/* Subtle Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-blue-500/5 to-transparent pointer-events-none"></div>
      
      {/* Header */}
      <div className="relative p-6">
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 flex items-center justify-center overflow-hidden transform transition-all duration-300 group-hover:scale-110 group-hover:rotate-6">
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
                      ? 'bg-gradient-to-r from-purple-500/10 to-blue-500/10 border-l-2 border-purple-500' 
                      : 'hover:bg-gradient-to-r hover:from-purple-500/5 hover:to-blue-500/5 hover:translate-x-1'
                    }
                  `}
                >
                  {/* Hover Shimmer */}
                  <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
                  
                  <div className="p-1.5 rounded-lg transition-all duration-300">
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
                </Button>
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
