import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { api, clearSession, getStoredUser, getToken, setSession } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser());
  const [token, setToken] = useState(getToken());
  const [loading, setLoading] = useState(Boolean(getToken()));

  useEffect(() => {
    let ignore = false;

    async function restoreProfile() {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const profile = await api.profile();
        if (!ignore) {
          setUser(profile);
          setSession(token, profile);
        }
      } catch {
        if (!ignore) {
          clearSession();
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!ignore) setLoading(false);
      }
    }

    restoreProfile();

    return () => {
      ignore = true;
    };
  }, [token]);

  async function login(credentials) {
    const response = await api.login(credentials);
    setSession(response.token, response.user);
    setToken(response.token);
    setUser(response.user);
    return response;
  }

  async function register(data) {
    return api.register(data);
  }

  async function refreshProfile() {
    const profile = await api.profile();
    setUser(profile);
    setSession(token, profile);
    return profile;
  }

  async function updateProfile(data) {
    const response = await api.updateProfile(data);
    const nextUser = response.user || response;
    setUser(nextUser);
    setSession(token, nextUser);
    return response;
  }

  function logout() {
    clearSession();
    setToken(null);
    setUser(null);
  }

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      isAuthenticated: Boolean(token && user),
      role: user?.role || user?.profile?.role,
      login,
      register,
      logout,
      refreshProfile,
      updateProfile,
    }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
