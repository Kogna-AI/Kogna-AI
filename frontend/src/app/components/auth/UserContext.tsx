"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { User as SupabaseUser } from "@supabase/supabase-js";
import { supabase } from "../../../lib/supabaseClient";
import { useRouter } from "next/navigation";
import api from "../../../services/api";

// Supabase client is imported from `src/lib/supabaseClient`

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
          console.debug("[UserContext] init - storing access token (length):", session.access_token?.length);
          localStorage.setItem("token", session.access_token);
        }

        // Mark as authenticated BEFORE loading backend profile
        setIsAuthenticated(true);

        // Load backend user profile
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

        const currentPath = typeof window !== "undefined" ? window.location.pathname : "";

        if (event === "SIGNED_IN" && session?.user) {
          // Store token
          if (session.access_token) {
            console.debug("[UserContext] SIGNED_IN - storing access token (len):", session.access_token?.length);
            localStorage.setItem("token", session.access_token);
          }

          setIsAuthenticated(true);
          await loadBackendUser(session.user);

          // Only redirect if NOT already on home
          if (currentPath !== "/") {
            console.debug(`[UserContext] SIGNED_IN - redirecting from ${currentPath} to /`);
            router.push("/");
          } else {
            console.debug("[UserContext] SIGNED_IN - already on home, skipping redirect");
          }
        }

        if (event === "SIGNED_OUT") {
          console.debug("[UserContext] SIGNED_OUT - clearing token and user");
          localStorage.removeItem("token");
          setUser(null);
          setIsAuthenticated(false);

          // Only redirect if not already on home
          if (currentPath !== "/") {
            console.debug(`[UserContext] SIGNED_OUT - redirecting from ${currentPath} to /`);
            router.push("/");
          } else {
            console.debug("[UserContext] SIGNED_OUT - already on home, skipping redirect");
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
      console.debug("[UserContext] loadBackendUser - fetching backend user for supabase id:", supabaseUser.id);
      const backendUser: BackendUser = await api.getUserBySupabaseId(supabaseUser.id);
      console.debug("[UserContext] loadBackendUser - backend user:", backendUser);

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
    } catch (err) {
      console.warn("[UserContext] loadBackendUser - failed to get backend user, falling back to supabase-only user:", err);
      setUser({
        ...supabaseUser,
        id: supabaseUser.id,
        name: supabaseUser.email ?? "",
        role: "member",
      });
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
      value={{ user, isAuthenticated, loading, logout }}
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


//old one

// "use client"
// import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
// import { api } from '@/services/api';

// interface User {
//   id: string;
//   name: string;
//   email: string;
//   role: 'founder' | 'executive' | 'manager' | 'member';
//   organization_id?: number;
//   avatar?: string;
//   preferences: {
//     theme: 'light' | 'dark' | 'system';
//     notifications: boolean;
//     twoWaySync: boolean;
//   };
// }

// interface UserContextType {
//   user: User | null;
//   isAuthenticated: boolean;
//   loading: boolean;
//   login: (email: string, password: string) => Promise<boolean>;
//   logout: () => void;
//   updateUserPreferences: (preferences: Partial<User['preferences']>) => void;
// }

// const UserContext = createContext<UserContextType | undefined>(undefined);

// export function UserProvider({ children }: { children: ReactNode }) {
//   const [user, setUser] = useState<User | null>(null);
//   const [isAuthenticated, setIsAuthenticated] = useState(false);
//   const [loading, setLoading] = useState(true);

//   useEffect(() => {
//     // Check for existing session and validate token
//     const checkAuth = async () => {
//       const token = localStorage.getItem('token');
//       const savedUser = localStorage.getItem('kognadash_user');

//       if (token && savedUser) {
//         try {
//           // Validate token by fetching current user
//           const response = await api.getCurrentUser();
//           const backendUser = response.data || response;

//           // Convert backend user format to frontend User format
//           const userData: User = {
//             id: backendUser.id?.toString() || backendUser.id,
//             name: `${backendUser.first_name} ${backendUser.second_name || ''}`.trim(),
//             email: backendUser.email,
//             role: backendUser.role || 'member',
//             organization_id: backendUser.organization_id,
//             preferences: JSON.parse(savedUser).preferences || {
//               theme: 'light',
//               notifications: true,
//               twoWaySync: true
//             }
//           };

//           setUser(userData);
//           setIsAuthenticated(true);
//         } catch (error) {
//           console.error('Token validation failed:', error);
//           // Clear invalid session
//           localStorage.removeItem('token');
//           localStorage.removeItem('kognadash_user');
//           setUser(null);
//           setIsAuthenticated(false);
//         }
//       }
//       setLoading(false);
//     };

//     checkAuth();
//   }, []);

//   const login = async (email: string, password: string): Promise<boolean> => {
//     try {
//       setLoading(true);
//       const response = await api.login(email, password);

//       // Response format: { success: true, token: "...", user: {...} }
//       const { token, user: backendUser } = response;

//       // Store token
//       localStorage.setItem('token', token);

//       // Convert backend user to frontend User format
//       const userData: User = {
//         id: backendUser.id?.toString() || backendUser.id,
//         name: `${backendUser.first_name} ${backendUser.second_name || ''}`.trim(),
//         email: backendUser.email,
//         role: backendUser.role || 'member',
//         organization_id: backendUser.organization_id,
//         preferences: {
//           theme: 'light',
//           notifications: true,
//           twoWaySync: true
//         }
//       };

//       setUser(userData);
//       setIsAuthenticated(true);
//       localStorage.setItem('kognadash_user', JSON.stringify(userData));
//       setLoading(false);

//       return true;
//     } catch (error) {
//       console.error('Login failed:', error);
//       setLoading(false);
//       return false;
//     }
//   };

//   const logout = () => {
//     setUser(null);
//     setIsAuthenticated(false);
//     localStorage.removeItem('token');
//     localStorage.removeItem('kognadash_user');
//   };

//   const updateUserPreferences = (newPreferences: Partial<User['preferences']>) => {
//     if (user) {
//       const updatedUser = {
//         ...user,
//         preferences: { ...user.preferences, ...newPreferences }
//       };
//       setUser(updatedUser);
//       localStorage.setItem('kognadash_user', JSON.stringify(updatedUser));
//     }
//   };

//   return (
//     <UserContext.Provider value={{
//       user,
//       isAuthenticated,
//       loading,
//       login,
//       logout,
//       updateUserPreferences
//     }}>
//       {children}
//     </UserContext.Provider>
//   );
// }

// export function useUser() {
//   const context = useContext(UserContext);
//   if (context === undefined) {
//     throw new Error('useUser must be used within a UserProvider');
//   }
//   return context;
// }
