"use client"
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'founder' | 'executive' | 'manager' | 'member';
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
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  updateUserPreferences: (preferences: Partial<User['preferences']>) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

// Mock user data - in real app this would come from your backend
const mockUsers: User[] = [
  {
    id: '1',
    name: 'Allen',
    email: 'allen@kognadash.com',
    role: 'founder',
    preferences: {
      theme: 'light',
      notifications: true,
      twoWaySync: true
    }
  },
  {
    id: '2',
    name: 'Sarah Chen',
    email: 'sarah@kognadash.com',
    role: 'executive',
    preferences: {
      theme: 'light',
      notifications: true,
      twoWaySync: false
    }
  }
];

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check for existing session - for demo, we'll auto-login as Allen
    const savedUser = localStorage.getItem('kognadash_user');
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
      setIsAuthenticated(true);
    } else {
      // Auto-login as Allen for demo
      const allenUser = mockUsers[0];
      setUser(allenUser);
      setIsAuthenticated(true);
      localStorage.setItem('kognadash_user', JSON.stringify(allenUser));
    }
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    // Mock authentication - in real app this would call your backend
    const foundUser = mockUsers.find(u => u.email === email);
    if (foundUser && password === 'demo123') {
      setUser(foundUser);
      setIsAuthenticated(true);
      localStorage.setItem('kognadash_user', JSON.stringify(foundUser));
      return true;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
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