import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { login as apiLogin, logout as apiLogout, refresh as apiRefresh, getMe } from "../api/client";
import { setAccessToken, clearAccessToken, setOnSessionExpired } from "../api/tokenStore";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState("loading"); // "loading" | "authenticated" | "unauthenticated"

  const login = useCallback(async (email, password) => {
    const data = await apiLogin(email, password);
    setAccessToken(data.access_token);
    setUser(data.user);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } finally {
      clearAccessToken();
      setUser(null);
      setStatus("unauthenticated");
    }
  }, []);

  useEffect(() => {
    setOnSessionExpired(() => {
      clearAccessToken();
      setUser(null);
      setStatus("unauthenticated");
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    apiRefresh()
      .then((data) => {
        if (cancelled) return;
        setAccessToken(data.access_token);
        return getMe();
      })
      .then((me) => {
        if (cancelled || !me) return;
        setUser(me);
        setStatus("authenticated");
      })
      .catch(() => {
        if (!cancelled) setStatus("unauthenticated");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return <AuthContext.Provider value={{ user, status, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
