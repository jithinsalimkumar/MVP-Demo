'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';

interface AuthContextType {
  isAuthenticated: boolean;
  username: string | null;
  login: (token: string, username: string) => void;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  username: null,
  login: () => {},
  logout: () => {},
  loading: true,
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [username, setUsername] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = localStorage.getItem('lead_outreach_token');
    const savedUser = localStorage.getItem('lead_outreach_user');

    if (token) {
      setIsAuthenticated(true);
      setUsername(savedUser || 'admin');
    } else {
      setIsAuthenticated(false);
      setUsername(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated && pathname !== '/login') {
        router.push('/login');
      } else if (isAuthenticated && pathname === '/login') {
        router.push('/dashboard');
      }
    }
  }, [isAuthenticated, loading, pathname, router]);

  const login = (token: string, user: string) => {
    localStorage.setItem('lead_outreach_token', token);
    localStorage.setItem('lead_outreach_user', user);
    setIsAuthenticated(true);
    setUsername(user);
    router.push('/dashboard');
  };

  const logout = () => {
    localStorage.removeItem('lead_outreach_token');
    localStorage.removeItem('lead_outreach_user');
    setIsAuthenticated(false);
    setUsername(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, username, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
