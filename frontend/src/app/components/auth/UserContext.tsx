"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import api, { setAccessToken, getAccessToken } from "@/services/api";
import { cleanupOldSupabaseAuth } from "@/utils/cleanupOldAuth";

export interface BackendUserRbac {
  role_name: string;
  role_level: number;
  permissions: string[];
  team_ids: string[];
}

export interface BackendUser {
  id: string;
  email: string;
  first_name?: string;
  second_name?: string;
  role?: string;
  organization_id?: string;
  organization_name?: string;
  created_at?: string;
  rbac?: BackendUserRbac;
}

interface SignupPayload {
  first_name: string;
  second_name?: string;
  email: string;
  password: string;
  role?: string;
  organization: string;
}

interface SignupResult {
  success: boolean;
  error?: string;
}

interface UserContextType {
  user: BackendUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  refreshUser: () => Promise<void>;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  signup: (payload: SignupPayload) => Promise<SignupResult>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

// Cache user object in sessionStorage for instant availability on refresh
function getCachedUser(): BackendUser | null {
  if (typeof window === 'undefined') return null;
  try {
    const cached = sessionStorage.getItem('cached-user');
    return cached ? JSON.parse(cached) : null;
  } catch {
    return null;
  }
}

function setCachedUser(user: BackendUser | null) {
  if (typeof window === 'undefined') return;
  try {
    if (user) {
      sessionStorage.setItem('cached-user', JSON.stringify(user));
    } else {
      sessionStorage.removeItem('cached-user');
    }
  } catch {
    // Ignore storage errors
  }
}

export function UserProvider({ children }: { children: React.ReactNode }) {
  // Load cached user immediately if available
  const [user, setUser] = useState<BackendUser | null>(getCachedUser());
  // Optimistic authentication: if token exists in memory, assume authenticated
  const [isAuthenticated, setIsAuthenticated] = useState(!!getAccessToken());
  // Only show loading if we don't have a token (need to check refresh)
  const [loading, setLoading] = useState(!getAccessToken());

  // ---------- CORE: stable fetch ----------
  const fetchCurrentUser = useCallback(async (showLoading = false) => {
    // Only show loading if explicitly requested (e.g., on login) or no token exists
    if (showLoading) {
      setLoading(true);
    }

    // Check if we have an access token in memory
    const token = getAccessToken();
    if (!token) {
      // No token in memory; try to refresh using httpOnly cookie
      try {
        setLoading(true);
        await api.refreshToken();
        // Token refreshed successfully, now fetch user
      } catch {
        // No valid session; user must log in
        setLoading(false);
        setIsAuthenticated(false);
        return;
      }
    }

    try {
      const res = await api.getCurrentUser();
      const finalUser = res && typeof res === "object" && "user" in res ? (res as any).user : res;

      setUser(finalUser as BackendUser);
      setCachedUser(finalUser as BackendUser); // Cache for next refresh
      setIsAuthenticated(true);
    } catch (err) {
      console.warn("getCurrentUser failed", err);
      setUser(null);
      setCachedUser(null);
      setIsAuthenticated(false);
      setAccessToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // ---------- INIT: run ONCE ----------
  useEffect(() => {
    // Clean up old Supabase auth data before initializing new auth
    cleanupOldSupabaseAuth();
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  // ---------- PUBLIC API ----------
  const refreshUser = useCallback(async () => {
    await fetchCurrentUser(true); // Show loading when manually refreshing
  }, [fetchCurrentUser]);

  const login = async (email: string, password: string) => {
    try {
      const res = await api.login(email, password);

      // api.login already stores token in memory via setAccessToken
      if (!res.access_token) {
        return false;
      }

      await fetchCurrentUser(true); // Show loading during login
      return true;
    } catch (err) {
      console.error("Login failed", err);
      return false;
    }
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch (err) {
      console.error("Logout failed", err);
    } finally {
      // Always clear local state and cache
      setUser(null);
      setCachedUser(null);
      setIsAuthenticated(false);
      setAccessToken(null);
    }
  };

  const signup = async (payload: SignupPayload): Promise<SignupResult> => {
    try {
      await api.register(payload);
      return { success: true };
    } catch (err) {
      console.error("Signup failed", err);
      const message =
        err instanceof Error && err.message
          ? err.message
          : "Failed to create account";
      return { success: false, error: message };
    }
  };

  return (
    <UserContext.Provider
      value={{
        user,
        isAuthenticated,
        loading,
        refreshUser,
        login,
        logout,
        signup,
      }}
    >
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used inside UserProvider");
  return ctx;
}
