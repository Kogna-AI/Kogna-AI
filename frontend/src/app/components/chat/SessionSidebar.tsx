'use client';

/**
 * SessionSidebar - Multi-Session History Browser
 *
 * Claude.ai-style conversation history sidebar with:
 * - Grouped sessions by time period (Today, Yesterday, Last 7 days, etc.)
 * - Infinite scroll pagination
 * - Auto-generated session titles
 * - Message count badges
 * - Active session highlighting
 *
 * Usage:
 * ```tsx
 * <SessionSidebar
 *   sessions={sessions}
 *   currentSessionId={currentSessionId}
 *   onSelectSession={handleSessionSwitch}
 *   onLoadMore={loadMoreSessions}
 *   hasMore={hasMoreSessions}
 *   loading={loading}
 * />
 * ```
 */

import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import type { SessionData } from '@/services/api';

interface SessionSidebarProps {
  sessions: SessionData[];
  currentSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onLoadMore: () => void;
  hasMore: boolean;
  loading: boolean;
}

export function SessionSidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onLoadMore,
  hasMore,
  loading
}: SessionSidebarProps) {
  // Group sessions by time period
  const groupedSessions = groupByTimePeriod(sessions);

  // Infinite scroll handler
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;

    // Load more when scrolled to bottom (with 1.5x client height threshold)
    if (scrollHeight - scrollTop <= clientHeight * 1.5 && hasMore && !loading) {
      onLoadMore();
    }
  };

  return (
    <div className="w-64 border-r bg-background flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b">
        <h2 className="font-semibold text-lg">Conversations</h2>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto" onScroll={handleScroll}>
        <div className="p-2 space-y-4">
          {Object.entries(groupedSessions).map(([period, periodSessions]) => (
            <div key={period}>
              <h3 className="text-xs font-medium text-muted-foreground px-2 mb-2">
                {period}
              </h3>
              <div className="space-y-1">
                {periodSessions.map(session => (
                  <SessionItem
                    key={session.id}
                    session={session}
                    isActive={session.id === currentSessionId}
                    onClick={() => onSelectSession(session.id)}
                  />
                ))}
              </div>
            </div>
          ))}

          {loading && (
            <div className="text-center py-4 text-sm text-muted-foreground">
              Loading more...
            </div>
          )}

          {!hasMore && sessions.length > 0 && (
            <div className="text-center py-4 text-xs text-muted-foreground">
              No more conversations
            </div>
          )}

          {sessions.length === 0 && !loading && (
            <div className="text-center py-8 text-sm text-muted-foreground">
              No conversations yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface SessionItemProps {
  session: SessionData;
  isActive: boolean;
  onClick: () => void;
}

function SessionItem({ session, isActive, onClick }: SessionItemProps) {
  // Use auto_title (first message preview) or fallback to title or "New Chat"
  const displayTitle = session.title || session.auto_title || 'New Chat';

  // Format time ago (always use created_at so sessions stay in their original time period)
  const timeAgo = formatDistanceToNow(new Date(session.created_at), { addSuffix: true });

  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
        isActive
          ? 'bg-primary/10 text-primary font-medium'
          : 'hover:bg-muted text-foreground'
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm truncate">{displayTitle}</p>
          <p className="text-xs text-muted-foreground">{timeAgo}</p>
        </div>
        {session.message_count > 0 && (
          <span className="text-xs text-muted-foreground shrink-0">
            {session.message_count}
          </span>
        )}
      </div>
    </button>
  );
}

/**
 * Group sessions by time period for organized display
 *
 * @param sessions - Array of sessions to group
 * @returns Object with time period keys and session arrays
 */
function groupByTimePeriod(sessions: SessionData[]): Record<string, SessionData[]> {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const lastWeek = new Date(today);
  lastWeek.setDate(lastWeek.getDate() - 7);
  const lastMonth = new Date(today);
  lastMonth.setDate(lastMonth.getDate() - 30);

  const groups: Record<string, SessionData[]> = {
    'Today': [],
    'Yesterday': [],
    'Last 7 days': [],
    'Last 30 days': [],
    'Older': []
  };

  sessions.forEach(session => {
    const date = new Date(session.created_at);

    if (date >= today) {
      groups['Today'].push(session);
    } else if (date >= yesterday) {
      groups['Yesterday'].push(session);
    } else if (date >= lastWeek) {
      groups['Last 7 days'].push(session);
    } else if (date >= lastMonth) {
      groups['Last 30 days'].push(session);
    } else {
      groups['Older'].push(session);
    }
  });

  // Remove empty groups
  return Object.fromEntries(
    Object.entries(groups).filter(([_, sessions]) => sessions.length > 0)
  );
}
