"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import api from "@/services/api";

interface BackendUser {
  id: string;
  email: string;
  first_name?: string;
  second_name?: string;
  role?: string;
  organization_id?: number;
}

interface UserContextType {
  user: BackendUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  refreshUser: () => Promise<void>;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<BackendUser | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // ---------- CORE: stable fetch ----------
  const fetchCurrentUser = useCallback(async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const res = await api.getCurrentUser();
      const finalUser = "user" in res ? res.user : res;

      setUser(finalUser as BackendUser);
      setIsAuthenticated(true);
    } catch (err) {
      console.warn("getCurrentUser failed", err);
      // DO NOT clear token here during OAuth
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  }, []);

  // ---------- INIT: run ONCE ----------
  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  // ---------- PUBLIC API ----------
  const refreshUser = useCallback(async () => {
    setLoading(true);
    await fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = async (email: string, password: string) => {
    try {
      const res = await api.login(email, password);

      localStorage.setItem("token", res.access_token);

      await fetchCurrentUser();

      return true;
    } catch (err) {
      console.error("Login failed", err);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    setIsAuthenticated(false);
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
