"use client";

import { X } from "lucide-react";
import type { ReactNode } from "react";

interface TileExpandModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  toolName?: string;
  iframeUrl?: string;
  /** Fallback content when there's no iframe URL */
  children?: ReactNode;
}

export function TileExpandModal({
  isOpen,
  onClose,
  title,
  toolName,
  iframeUrl,
  children,
}: TileExpandModalProps) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-[90vw] h-[85vh] bg-background rounded-xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between h-14 px-5 border-b border-border bg-muted/40 shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold text-foreground">{title}</h2>
            {toolName && (
              <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground bg-muted rounded-full px-2.5 py-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                {toolName}
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 bg-muted/20 relative">
          {iframeUrl ? (
            <iframe
              src={iframeUrl}
              title={title}
              className="w-full h-full border-0"
              sandbox="allow-scripts allow-same-origin allow-popups"
            />
          ) : children ? (
            <div className="w-full h-full overflow-auto p-6">{children}</div>
          ) : (
            /* Skeleton fallback */
            <div className="w-full h-full flex flex-col items-center justify-center gap-4 text-muted-foreground">
              <div className="space-y-4 w-full max-w-2xl px-8">
                <div className="h-8 w-72 bg-muted rounded animate-pulse" />
                <div className="grid grid-cols-3 gap-5">
                  <div className="h-48 bg-muted rounded-lg animate-pulse col-span-2" />
                  <div className="h-48 bg-muted rounded-lg animate-pulse" />
                  <div className="h-48 bg-muted rounded-lg animate-pulse" />
                  <div className="h-48 bg-muted rounded-lg animate-pulse col-span-2" />
                </div>
              </div>
              <p className="text-sm font-medium">Waiting for connection...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
