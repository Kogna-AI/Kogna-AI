"use client";

import { type User as SupabaseUser } from "@supabase/supabase-js";
import { useRouter } from "next/navigation";
import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";
import { supabase } from "../../../lib/supabaseClient";
import api from "../../../services/api";

// Backend user type
export interface BackendUser {
  id: string;
  first_name?: string;
  second_name?: string;
  role?: string;
  organization_id?: number;
  email?: string;
  supabase_id?: string;
}

// Combined User type
export type MergedUser = SupabaseUser & {
  id: string; // Backend user ID
  name?: string;
  role?: string;
  organization_id?: number;
};

// Context interface
interface UserContextType {
  user: MergedUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  signup: (data: {
    first_name: string;
    second_name: string;
    email: string;
    password: string;
    role: string;
    organization: string;
  }) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
}

// Create context
const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const router = useRouter();

  const [user, setUser] = useState<MergedUser | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      try {
        console.debug("[UserContext] init - checking supabase session...");
        const {
          data: { session },
        } = await supabase.auth.getSession();

        console.debug("[UserContext] init - session:", session);

        if (!session?.user) {
          console.debug("[UserContext] init - no session -> unauthenticated");
          setIsAuthenticated(false);
          setUser(null);
          setLoading(false);
          return;
        }

        // Supabase session exists → store token
        if (session.access_token) {
          console.debug(
            "[UserContext] init - storing access token (length):",
            session.access_token?.length
          );
          localStorage.setItem("token", session.access_token);
        }

        // Mark as authenticated BEFORE loading backend profile
        setIsAuthenticated(true);
        await loadBackendUser(session.user);
        setLoading(false);
      } catch (err) {
        console.error("[UserContext] init - error while getting session:", err);
        setIsAuthenticated(false);
        setUser(null);
        setLoading(false);
      }
    };

    init();
  }, []);

  useEffect(() => {
    console.debug("[UserContext] setting up auth state change subscription");
    const { data: subscription } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.debug("[UserContext] auth event:", event, session);

        const currentPath =
          typeof window !== "undefined" ? window.location.pathname : "";

        if (event === "SIGNED_IN" && session?.user) {
          // Store token
          if (session.access_token) {
            console.debug(
              "[UserContext] SIGNED_IN - storing access token (len):",
              session.access_token?.length
            );
            localStorage.setItem("token", session.access_token);
          }

          setIsAuthenticated(true);
          await loadBackendUser(session.user);

          // Only redirect if NOT already on home
          if (currentPath !== "/") {
            console.debug(
              `[UserContext] SIGNED_IN - redirecting from ${currentPath} to /`
            );
            router.push("/");
          } else {
            console.debug(
              "[UserContext] SIGNED_IN - already on home, skipping redirect"
            );
          }
        }

        if (event === "SIGNED_OUT") {
          console.debug("[UserContext] SIGNED_OUT - clearing token and user");
          localStorage.removeItem("token");
          setUser(null);
          setIsAuthenticated(false);

          // Only redirect if not already on home
          if (currentPath !== "/") {
            console.debug(
              `[UserContext] SIGNED_OUT - redirecting from ${currentPath} to /`
            );
            router.push("/");
          } else {
            console.debug(
              "[UserContext] SIGNED_OUT - already on home, skipping redirect"
            );
          }
        }
      }
    );

    return () => {
      console.debug("[UserContext] unsubscribing auth state change");
      try {
        subscription.subscription.unsubscribe();
      } catch (err) {
        console.warn("[UserContext] error unsubscribing:", err);
      }
    };
  }, [router]);

  const loadBackendUser = async (supabaseUser: SupabaseUser) => {
    try {
      console.debug(
        "[UserContext] loadBackendUser - fetching backend user for supabase id:",
        supabaseUser.id
      );
      const backendUser: BackendUser = await api.getUserBySupabaseId(
        supabaseUser.id
      );
      console.debug(
        "[UserContext] loadBackendUser - backend user:",
        backendUser
      );

      const mergedUser: MergedUser = {
        ...supabaseUser,
        id: backendUser.id,
        name: [backendUser.first_name, backendUser.second_name]
          .filter(Boolean)
          .join(" "),
        role: backendUser.role,
        organization_id: backendUser.organization_id,
      };

      setUser(mergedUser);
      setLoading(false);
    } catch (err) {
      console.warn(
        "[UserContext] loadBackendUser - failed to get backend user, falling back to supabase-only user:",
        err
      );
      setUser({
        ...supabaseUser,
        id: supabaseUser.id,
        name: supabaseUser.email ?? "",
        role: "member",
      });
      setLoading(false);
    }
  };

  // Signup
  const signup = async ({
    first_name,
    second_name,
    email,
    password,
    role,
    organization,
  }: {
    first_name: string;
    second_name: string;
    email: string;
    password: string;
    role: string;
    organization: string;
  }) => {
    try {
      // Create backend user
      console.debug("[UserContext] signup - creating backend user");
      await api.register({
        email,
        first_name,
        second_name,
        role,
        organization: organization,
        password,
      });

      return { success: true };
    } catch (err) {
      console.error("[UserContext] signup - unexpected error:", err);
      return {
        success: false,
        error: "Unable to create account. Please try again.",
      };
    }
  };

  // Logout
  const logout = async () => {
    console.debug("[UserContext] logout - signing out");
    localStorage.removeItem("token");
    try {
      await supabase.auth.signOut();
    } catch (err) {
      console.error("[UserContext] logout - signOut error:", err);
    }
  };

  return (
    <UserContext.Provider
      value={{ user, isAuthenticated, loading, signup, logout }}
    >
      {children}
    </UserContext.Provider>
  );
}

// Hook for consuming context
export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within a UserProvider");
  return ctx;
}
