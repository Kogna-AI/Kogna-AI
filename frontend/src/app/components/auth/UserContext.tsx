"use client"
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '@/services/api';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'founder' | 'executive' | 'manager' | 'member';
  organization_id?: number;
  avatar?: string;
  preferences: {
    theme: 'light' | 'dark' | 'system';
    notifications: boolean;
    twoWaySync: boolean;
  };
}

interface UserContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  updateUserPreferences: (preferences: Partial<User['preferences']>) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session and validate token
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      const savedUser = localStorage.getItem('kognadash_user');

      if (token && savedUser) {
        try {
          // Validate token by fetching current user
          const response = await api.getCurrentUser();
          const backendUser = response.data || response;

          // Convert backend user format to frontend User format
          const userData: User = {
            id: backendUser.id?.toString() || backendUser.id,
            name: `${backendUser.first_name} ${backendUser.second_name || ''}`.trim(),
            email: backendUser.email,
            role: backendUser.role || 'member',
            organization_id: backendUser.organization_id,
            preferences: JSON.parse(savedUser).preferences || {
              theme: 'light',
              notifications: true,
              twoWaySync: true
            }
          };

          setUser(userData);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Token validation failed:', error);
          // Clear invalid session
          localStorage.removeItem('token');
          localStorage.removeItem('kognadash_user');
          setUser(null);
          setIsAuthenticated(false);
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await api.login(email, password);

      // Response format: { success: true, token: "...", user: {...} }
      const { token, user: backendUser } = response;

      // Store token
      localStorage.setItem('token', token);

      // Convert backend user to frontend User format
      const userData: User = {
        id: backendUser.id?.toString() || backendUser.id,
        name: `${backendUser.first_name} ${backendUser.second_name || ''}`.trim(),
        email: backendUser.email,
        role: backendUser.role || 'member',
        organization_id: backendUser.organization_id,
        preferences: {
          theme: 'light',
          notifications: true,
          twoWaySync: true
        }
      };

      setUser(userData);
      setIsAuthenticated(true);
      localStorage.setItem('kognadash_user', JSON.stringify(userData));
      setLoading(false);

      return true;
    } catch (error) {
      console.error('Login failed:', error);
      setLoading(false);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('token');
    localStorage.removeItem('kognadash_user');
  };

  const updateUserPreferences = (newPreferences: Partial<User['preferences']>) => {
    if (user) {
      const updatedUser = {
        ...user,
        preferences: { ...user.preferences, ...newPreferences }
      };
      setUser(updatedUser);
      localStorage.setItem('kognadash_user', JSON.stringify(updatedUser));
    }
  };

  return (
    <UserContext.Provider value={{
      user,
      isAuthenticated,
      loading,
      login,
      logout,
      updateUserPreferences
    }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}
