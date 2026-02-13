"use client";

import { Share2, Bell, LogOut, Settings } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRef, useEffect, useState } from "react";
import { useUser } from "../auth/UserContext";
import { Avatar, AvatarFallback } from "../../ui/avatar";

interface DashboardTopNavProps {
  onKogniiToggle: () => void;
  onNotificationsToggle: () => void;
  onShare?: () => void;
}

function getInitials(user: any): string {
  if (!user) return "?";
  const first = (user.first_name || "").trim().charAt(0);
  const second = (user.second_name || "").trim().charAt(0);
  if (first && second) return `${first}${second}`.toUpperCase();
  if (user.email) return user.email.slice(0, 2).toUpperCase();
  return "?";
}

export function DashboardTopNav({
  onKogniiToggle,
  onNotificationsToggle,
  onShare,
}: DashboardTopNavProps) {
  const { user, logout } = useUser();
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const isSettings = pathname === "/settings";

  useEffect(() => {
    if (!menuOpen) return;
    const close = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [menuOpen]);

  const initials = getInitials(user);

  return (
    <header
      className="sticky top-0 z-40 flex-shrink-0 h-12 w-full border-b border-border bg-background"
      role="banner"
    >
      <div className="flex h-full items-center justify-end gap-4 md:gap-6 px-4 md:px-6">
        <button
          type="button"
          onClick={onKogniiToggle}
          className="inline-flex items-center gap-2.5 rounded-lg px-4 py-2 text-sm font-bold text-white bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 transition-all duration-200 border-0"
        >
          <span
            className="relative flex h-2.5 w-2.5 shrink-0"
            aria-hidden
          >
            <span className="absolute inline-flex h-full w-full animate-pulse rounded-full bg-white/80" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-white ring-2 ring-white/50" />
          </span>
          <span>Ask Kogna</span>
          <span className="rounded bg-white/20 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
            AI
          </span>
        </button>

        <button
          type="button"
          onClick={onNotificationsToggle}
          className="relative p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded hover:bg-muted/60"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute right-0 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-medium text-white">
            3
          </span>
        </button>

        {/* User avatar — click to open Sign Out */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen((o) => !o)}
            className="rounded-full focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            aria-label="User menu"
          >
            <Avatar className="h-9 w-9 border-2 border-border/80">
              <AvatarFallback
                className="bg-[#6b7355] text-white/90 text-sm font-medium"
              >
                {initials}
              </AvatarFallback>
            </Avatar>
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-full mt-1.5 py-1 min-w-[140px] rounded-lg border border-border bg-popover z-50">
              <Link
                href="/settings"
                onClick={() => setMenuOpen(false)}
                className={`flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-colors ${
                  isSettings
                    ? "text-foreground bg-muted/60"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                }`}
              >
                <Settings className="h-4 w-4" />
                Settings
              </Link>
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  logout();
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-colors"
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </button>
            </div>
          )}
        </div>

        {onShare && (
          <button
            type="button"
            onClick={onShare}
            className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            <Share2 className="h-4 w-4" />
            <span>Share</span>
          </button>
        )}
      </div>
    </header>
  );
}
