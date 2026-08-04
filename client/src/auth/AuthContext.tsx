import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, setOnUnauthorized, setToken } from "../api";

interface AuthValue {
  email: string | null;
  authed: boolean;
  login(email: string, password: string): Promise<void>;
  register(email: string, password: string): Promise<void>;
  logout(): void;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [email, setEmail] = useState<string | null>(() =>
    localStorage.getItem("agent_email")
  );
  const [token, setTokenState] = useState<string | null>(() => {
    const t = localStorage.getItem("agent_token");
    setToken(t);
    return t;
  });

  useEffect(() => {
    const logoutHandler = () => {
      localStorage.removeItem("agent_token");
      localStorage.removeItem("agent_email");
      setToken(null);
      setTokenState(null);
      setEmail(null);
    };
    setOnUnauthorized(logoutHandler);
    return () => setOnUnauthorized(null);
  }, []);

  const value = useMemo<AuthValue>(() => {
    const login = async (em: string, pw: string) => {
      const { token: t } = await api.login(em, pw);
      localStorage.setItem("agent_token", t);
      localStorage.setItem("agent_email", em);
      setToken(t);
      setTokenState(t);
      setEmail(em);
    };
    return {
      email,
      authed: token !== null,
      login,
      register: async (em: string, pw: string) => {
        await api.register(em, pw);
        await login(em, pw);
      },
      logout: () => {
        localStorage.removeItem("agent_token");
        localStorage.removeItem("agent_email");
        setToken(null);
        setTokenState(null);
        setEmail(null);
      },
    };
  }, [email, token]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
