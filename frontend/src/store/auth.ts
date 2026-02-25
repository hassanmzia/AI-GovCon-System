"use client";

import { create } from "zustand";
import api from "@/lib/api";

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role?: "admin" | "executive" | "capture_manager" | "proposal_manager" | "viewer" | "user";
  is_mfa_enabled?: boolean;
  is_active?: boolean;
  date_joined?: string;
}

interface Tokens {
  access: string;
  refresh: string;
}

interface AuthState {
  user: User | null;
  tokens: Tokens | null;
  isAuthenticated: boolean;
  initialize: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  // Always null on init — reading localStorage here causes SSR/hydration mismatch
  // because the server has no localStorage and renders different HTML than the client.
  // Tokens are loaded lazily in initialize(), called from a useEffect (client-only).
  tokens: null,
  isAuthenticated: false,

  initialize: async () => {
    let { tokens, user } = get();

    // On first client-side call: read tokens from localStorage
    if (!tokens) {
      try {
        const raw = localStorage.getItem("auth-tokens");
        tokens = raw ? JSON.parse(raw) : null;
        if (tokens) set({ tokens });
      } catch {
        // Malformed JSON in localStorage — ignore
      }
    }

    if (!tokens?.access || user) return;
    try {
      const userResponse = await api.get("/auth/me/");
      set({ user: userResponse.data, isAuthenticated: true });
    } catch {
      // Token is invalid/expired — the api interceptor will redirect to /login
    }
  },

  login: async (username: string, password: string) => {
    const response = await api.post("/auth/token/", { username, password });
    const tokens: Tokens = {
      access: response.data.access,
      refresh: response.data.refresh,
    };

    localStorage.setItem("auth-tokens", JSON.stringify(tokens));

    set({ tokens, isAuthenticated: true });

    // Fetch user profile after login
    try {
      const userResponse = await api.get("/auth/me/");
      set({ user: userResponse.data });
    } catch {
      // User profile fetch is optional; token-based auth is sufficient
    }
  },

  logout: () => {
    localStorage.removeItem("auth-tokens");
    set({ user: null, tokens: null, isAuthenticated: false });
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  },

  refreshToken: async () => {
    const { tokens } = get();
    if (!tokens?.refresh) {
      throw new Error("No refresh token available");
    }

    const response = await api.post("/auth/token/refresh/", {
      refresh: tokens.refresh,
    });

    const updatedTokens: Tokens = {
      access: response.data.access,
      refresh: tokens.refresh,
    };

    localStorage.setItem("auth-tokens", JSON.stringify(updatedTokens));
    set({ tokens: updatedTokens });
  },

  setUser: (user: User) => {
    set({ user });
  },
}));
