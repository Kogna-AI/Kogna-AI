"use client";

import { Plus } from "lucide-react";
import type { ReactNode } from "react";

interface ConnectorOption {
  id: string;
  name: string;
  /** Large icon/logo element (~40px) */
  icon: ReactNode;
}

interface DashboardTileProps {
  title: string;
  subtitle?: string;
  /** Whether a tool is connected */
  isConnected: boolean;
  /** Name of the connected tool */
  connectedToolName?: string;
  /** Content to render when connected (preview) */
  connectedContent?: ReactNode;
  /** List of tools the user can connect — displayed as large icon cards */
  connectorOptions?: ConnectorOption[];
  /** Called when user selects a connector */
  onConnect?: (connectorId: string) => void;
  /** Called when user clicks to expand the connected view */
  onExpand?: () => void;
  /** Whether this is a placeholder tile (e.g. CRM coming soon) */
  isPlaceholder?: boolean;
  /** Custom empty state content */
  emptyStateContent?: ReactNode;
  /** Optional className for the outer card */
  className?: string;
}

export function DashboardTile({
  title,
  subtitle,
  isConnected,
  connectedToolName,
  connectedContent,
  connectorOptions,
  onConnect,
  onExpand,
  isPlaceholder = false,
  emptyStateContent,
  className = "",
}: DashboardTileProps) {
  /* ---- Connected state ---- */
  if (isConnected && connectedContent) {
    return (
      <div
        className={`group relative rounded-xl border border-border bg-card overflow-hidden hover:border-purple-200 transition-all duration-200 flex flex-col ${className}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-border/60">
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          {connectedToolName && (
            <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground bg-muted/60 rounded-full px-2.5 py-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              {connectedToolName}
            </span>
          )}
        </div>

        {/* Preview content */}
        <div className="flex-1 p-5">{connectedContent}</div>

        {/* Hover overlay to expand */}
        {onExpand && (
          <button
            type="button"
            onClick={onExpand}
            className="absolute inset-0 flex items-center justify-center bg-white/40 dark:bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity duration-200 cursor-pointer z-10"
          >
            <span className="rounded-full bg-foreground text-background px-5 py-2.5 text-sm font-semibold">
              Expand View
            </span>
          </button>
        )}
      </div>
    );
  }

  /* ---- Empty / connect state ---- */
  return (
    <div
      className={`rounded-xl border border-border bg-card flex flex-col overflow-hidden ${className}`}
    >
      {emptyStateContent ? (
        emptyStateContent
      ) : (
        <div className="flex-1 flex flex-col px-5 py-5">
          {/* Title row */}
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-sm font-semibold text-foreground">{title}</h3>
            {isPlaceholder && (
              <span className="rounded-full bg-muted px-2.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                Coming Soon
              </span>
            )}
          </div>

          {subtitle && (
            <p className="text-xs text-muted-foreground mb-4">{subtitle}</p>
          )}

          {/* Large icon grid — "Available · Click to Connect" */}
          {connectorOptions && connectorOptions.length > 0 && (
            <div className="flex-1 flex flex-col">
              <p className="text-[11px] text-muted-foreground mb-3 font-medium">
                Available · Click to Connect
              </p>
              <div className="flex flex-wrap gap-3">
                {connectorOptions.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    disabled={isPlaceholder}
                    onClick={() => onConnect?.(opt.id)}
                    className="flex flex-col items-center justify-center gap-2 w-[80px] h-[80px] rounded-xl bg-muted/40 border border-border hover:bg-accent hover:border-foreground/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-muted/40 disabled:hover:border-border"
                  >
                    <span className="shrink-0">{opt.icon}</span>
                    <span className="text-[10px] font-medium text-muted-foreground leading-tight text-center px-1">
                      {opt.name}
                    </span>
                  </button>
                ))}

                {/* Add more placeholder */}
                {!isPlaceholder && (
                  <div className="flex items-center justify-center w-[80px] h-[80px] rounded-xl border-2 border-dashed border-border/60">
                    <Plus className="h-5 w-5 text-muted-foreground/40" />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
