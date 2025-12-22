"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import { useRouter } from "next/navigation";
import api from "@/services/api";

export interface BackendUser {
  first_name: string;
  second_name: string;
  id: string;
  email: string;
  organization_id: string;
  role: string;
  rbac: {
    role_name: string;
    role_level: number;
    permissions: string[];
    team_ids: string[];
  };
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
  const router = useRouter();

  const [user, setUser] = useState<BackendUser | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // ============================
  // CORE: single source of truth
  // ============================
  const fetchCurrentUser = useCallback(async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setUser(null);
      setIsAuthenticated(false);
      setLoading(false);
      return;
    }

    try {
      const me = await api.getCurrentUser(); // BackendUser only
      setUser(me);
      setIsAuthenticated(true);
    } catch (err) {
      console.warn("getCurrentUser failed", err);
      localStorage.removeItem("token");
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  }, []);

  // INIT once
  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  // PUBLIC API
  const refreshUser = useCallback(async () => {
    setLoading(true);
    await fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = async (email: string, password: string) => {
    try {
      await api.login(email, password);
      await fetchCurrentUser(); // <-- 关键：login 不 setUser
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
    router.push("/");
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
