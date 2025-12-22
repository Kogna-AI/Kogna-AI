"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api, { LoginUser } from "@/services/api";

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

export type AuthUser = LoginUser | BackendUser;

interface UserContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  signup: (data: any) => Promise<any>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  const [user, setUser] = useState<AuthUser | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const fullUser = await api.getCurrentUser(); // BackendUser
        setUser(fullUser);
        setIsAuthenticated(true);
      } catch {
        localStorage.removeItem("token");
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    init();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const res = await api.login(email, password);
      setUser(res.user); // LoginUser
      setIsAuthenticated(true);
      return true;
    } catch {
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    setIsAuthenticated(false);
    router.push("/");
  };

  const signup = async (form: any) => {
    return api.register(form);
  };

  return (
    <UserContext.Provider
      value={{ user, isAuthenticated, loading, login, logout, signup }}
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
