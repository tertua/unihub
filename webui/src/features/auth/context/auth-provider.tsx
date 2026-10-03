'use client';

/**
 * Client-side auth context backed by the Django JWT API.
 *
 * Holds the current user so the shell (sidebar, header, nav filtering) can
 * react to role changes without refetching.
 */

import { ApiRequestError } from '@/lib/api-client';
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import * as authService from '../api/service';
import type { LoginPayload, RegisterPayload, User } from '../api/types';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<User>;
  register: (payload: RegisterPayload) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (!authService.hasStoredSession()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser(await authService.me());
    } catch {
      // A dead/invalid token is not an error state here — just treat as signed out.
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (payload: LoginPayload) => {
    const nextUser = await authService.login(payload);
    setUser(nextUser);
    return nextUser;
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    await authService.register(payload);
    // Auto-login with the same credentials so the user lands signed in.
    const nextUser = await authService.login({
      username: payload.username,
      password: payload.password
    });
    setUser(nextUser);
    return nextUser;
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, login, register, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** Access the auth context. Throws when used outside the provider. */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}

export { ApiRequestError };
