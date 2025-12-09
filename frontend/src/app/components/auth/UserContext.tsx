"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  signup: (data: any) => Promise<any>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  const [user, setUser] = useState<BackendUser | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // ============================
  // 1. Initialize Auth State
  // ============================
  useEffect(() => {
    const init = async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const me = (await api.getCurrentUser()) as { user?: BackendUser }; // <-- FIXED
        const finalUser = "user" in me ? me.user : me;

        setUser(finalUser as BackendUser);
        setIsAuthenticated(true);
      } catch (err) {
        console.warn("Invalid token, logging out");
        localStorage.removeItem("token");
        setUser(null);
        setIsAuthenticated(false);
      }

      setLoading(false);
    };

    init();
  }, []);

  // ============================
  // 2. LOGIN
  // ============================
  const login = async (email: string, password: string) => {
    try {
      const res = await api.login(email, password); // <-- FIXED

      localStorage.setItem("token", res.access_token);
      setUser(res.user);
      setIsAuthenticated(true);

      return true;
    } catch (err) {
      console.error("Login failed:", err);
      return false;
    }
  };

  // ============================
  // 3. LOGOUT
  // ============================
  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    setIsAuthenticated(false);
    router.push("/");
  };

  // ============================
  // 4. SIGNUP
  // ============================
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

// Hook
export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used inside UserProvider");
  return ctx;
}
