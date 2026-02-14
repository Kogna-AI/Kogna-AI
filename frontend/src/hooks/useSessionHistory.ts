/**
 * useSessionHistory - Custom Hook for Session Management
 *
 * Provides session list management, session switching, and client-side caching
 * for the multi-session history feature.
 *
 * Features:
 * - Automatic session list loading on mount
 * - Infinite scroll pagination
 * - Client-side message caching for instant session switching
 * - Error handling and loading states
 */

import { useState, useEffect, useCallback } from 'react';
import { api, SessionData, MessageData } from '@/services/api';

interface UseSessionHistoryReturn {
  sessions: SessionData[];
  currentSessionId: string | null;
  messages: MessageData[];
  loading: boolean;
  error: string | null;
  loadSessions: () => Promise<void>;
  switchSession: (sessionId: string) => Promise<void>;
  loadMoreSessions: () => Promise<void>;
  hasMoreSessions: boolean;
  clearCache: () => void;
  invalidateSession: (sessionId: string) => void;
}

/**
 * Custom hook for managing session history
 *
 * @returns Session management state and methods
 *
 * @example
 * ```tsx
 * const {
 *   sessions,
 *   currentSessionId,
 *   messages,
 *   loading,
 *   switchSession,
 *   loadMoreSessions,
 *   hasMoreSessions
 * } = useSessionHistory();
 *
 * // Display sessions
 * {sessions.map(session => (
 *   <SessionItem
 *     key={session.id}
 *     session={session}
 *     isActive={session.id === currentSessionId}
 *     onClick={() => switchSession(session.id)}
 *   />
 * ))}
 * ```
 */
export function useSessionHistory(): UseSessionHistoryReturn {
  const [sessions, setSessions] = useState<SessionData[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMoreSessions, setHasMoreSessions] = useState(true);

  // Cache for loaded session messages (in-memory, client-side)
  const [messageCache, setMessageCache] = useState<Map<string, MessageData[]>>(
    new Map()
  );

  /**
   * Load initial sessions (first page)
   * Called automatically on mount
   */
  const loadSessions = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.getUserSessions(20, 0, 'created_at');
      setSessions(data);
      setOffset(20);
      setHasMoreSessions(data.length === 20);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load sessions';
      setError(errorMessage);
      console.error('Error loading sessions:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Load more sessions (infinite scroll)
   * Called when user scrolls to bottom of session list
   */
  const loadMoreSessions = useCallback(async () => {
    if (!hasMoreSessions || loading) {
      return;
    }

    setLoading(true);

    try {
      const data = await api.getUserSessions(20, offset, 'created_at');
      setSessions(prev => [...prev, ...data]);
      setOffset(prev => prev + 20);
      setHasMoreSessions(data.length === 20);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load more sessions';
      setError(errorMessage);
      console.error('Error loading more sessions:', err);
    } finally {
      setLoading(false);
    }
  }, [offset, hasMoreSessions, loading]);

  /**
   * Switch to a different session
   * Uses cache for instant loading if previously loaded
   *
   * @param sessionId - UUID of the session to switch to
   */
  const switchSession = useCallback(async (sessionId: string) => {
    setLoading(true);
    setError(null);
    setCurrentSessionId(sessionId);

    try {
      // Check cache first for instant loading
      if (messageCache.has(sessionId)) {
        setMessages(messageCache.get(sessionId)!);
        setLoading(false);
        return;
      }

      // Fetch from API
      const history = await api.getSessionHistory(sessionId);
      setMessages(history);

      // Cache the messages for future instant access
      setMessageCache(prev => new Map(prev).set(sessionId, history));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load session history';
      setError(errorMessage);
      console.error('Error switching session:', err);
      // Don't clear messages on error - keep showing previous session
    } finally {
      setLoading(false);
    }
  }, [messageCache]);

  /**
   * Clear message cache (useful for memory management with many sessions)
   * Can be called manually or on unmount
   */
  const clearCache = useCallback(() => {
    setMessageCache(new Map());
  }, []);

  /**
   * Invalidate cache for a specific session
   * Useful after sending a new message to force refresh
   *
   * @param sessionId - UUID of the session to invalidate
   */
  const invalidateSession = useCallback((sessionId: string) => {
    setMessageCache(prev => {
      const newCache = new Map(prev);
      newCache.delete(sessionId);
      return newCache;
    });
  }, []);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return {
    sessions,
    currentSessionId,
    messages,
    loading,
    error,
    loadSessions,
    switchSession,
    loadMoreSessions,
    hasMoreSessions,
    clearCache,
    invalidateSession,
  };
}
