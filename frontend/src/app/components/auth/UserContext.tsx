"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { createClient, User as SupabaseUser } from "@supabase/supabase-js";
import { useRouter } from "next/navigation";
import api from "../../../services/api";

// --- Initialize Supabase client ---
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
const supabase = createClient(supabaseUrl, supabaseAnonKey);

// --- Backend user model ---
export interface BackendUser {
  id: string;
  first_name?: string;
  second_name?: string;
  name?: string;
  role?: string;
  organization_id?: number;
  email?: string;
  supabase_id?: string;
}

// --- Combined user type for context ---
export type MergedUser = SupabaseUser & {
  id: string;
  name?: string;
  role?: string;
  organization_id?: number;
};

// --- UserContext type ---
interface UserContextType {
  user: MergedUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  logout: () => Promise<void>;
}

// --- Create React context ---
const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<MergedUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    async function initSession() {
      setLoading(true);
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (session?.access_token) {
        // Save the JWT for the backend API client (api.ts) to use
        localStorage.setItem("token", session.access_token);
      }

      if (session?.user) {
        const supabaseUser = session.user;
        setIsAuthenticated(true);
        try {
          const backendUser: BackendUser = await api.getUserBySupabaseId(
            supabaseUser.id
          );
          console.log(backendUser);
          const mergedUser: MergedUser = {
            ...supabaseUser,
            id: backendUser.id,
            name: [backendUser.first_name, backendUser.second_name]
              .filter(Boolean)
              .join(" "),
            role: backendUser.role || "member",
            organization_id: backendUser.organization_id,
          };
          setUser(mergedUser);
        } catch {
          setUser(supabaseUser);
        }
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
      setLoading(false);
    }

    initSession();

    const { data: listener } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (event === "SIGNED_IN" && session?.user) {
          if (session.access_token) {
            // Save the JWT for the backend API client (api.ts) to use
            localStorage.setItem("token", session.access_token);
          }
          initSession();
          router.push("/");
        } else if (event === "SIGNED_OUT") {
          setUser(null);
          setIsAuthenticated(false);
          router.push("/");
        }
      }
    );

    return () => listener.subscription.unsubscribe();
  }, [router]);

  // --- Logout function ---
  const logout = async () => {
    localStorage.removeItem("token");
    await supabase.auth.signOut();
  };

  return (
    <UserContext.Provider value={{ user, isAuthenticated, loading, logout }}>
      {children}
    </UserContext.Provider>
  );
}

// --- Hook for convenient access ---
export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
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
