import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  api,
  clearAuthToken,
  clearStoredUser,
  getAuthToken,
  getStoredUser,
  setAuthToken,
  setStoredUser,
} from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredUser());
  const [token, setToken] = useState(() => getAuthToken());
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    clearAuthToken();
    clearStoredUser();
    setToken(null);
    setUser(null);
  }, []);

  const refreshMe = useCallback(async () => {
    const currentToken = getAuthToken();
    if (!currentToken) {
      logout();
      return null;
    }

    try {
      const me = await api.getMe();
      setUser(me);
      setStoredUser(me);
      setToken(currentToken);
      return me;
    } catch {
      logout();
      return null;
    }
  }, [logout]);

  const loginUser = useCallback(async (credentials) => {
    const response = await api.login(credentials);
    const accessToken = response?.access_token;
    const userPayload = response?.user || null;
    if (!accessToken || !userPayload) {
      throw new Error("Respuesta de autenticación inválida.");
    }

    setAuthToken(accessToken);
    setStoredUser(userPayload);
    setToken(accessToken);
    setUser(userPayload);
    return userPayload;
  }, []);

  const registerUser = useCallback(async (payload) => {
    const response = await api.register(payload);
    const accessToken = response?.access_token;
    const userPayload = response?.user || null;
    if (!accessToken || !userPayload) {
      throw new Error("Respuesta de registro inválida.");
    }

    setAuthToken(accessToken);
    setStoredUser(userPayload);
    setToken(accessToken);
    setUser(userPayload);
    return userPayload;
  }, []);

  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      const currentToken = getAuthToken();
      if (!currentToken) {
        if (mounted) {
          setToken(null);
          setUser(null);
          setLoading(false);
        }
        return;
      }

      if (mounted) {
        setToken(currentToken);
      }

      try {
        const me = await api.getMe();
        if (!mounted) return;
        setUser(me);
        setStoredUser(me);
      } catch {
        if (!mounted) return;
        logout();
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    bootstrap();

    return () => {
      mounted = false;
    };
  }, [logout]);

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      isAuthenticated: Boolean(user && token),
      loginUser,
      registerUser,
      logout,
      refreshMe,
    }),
    [loading, loginUser, logout, refreshMe, registerUser, token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return context;
}
