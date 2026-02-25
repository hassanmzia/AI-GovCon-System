import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: inject JWT access token from localStorage
api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const tokensRaw = localStorage.getItem("auth-tokens");
      if (tokensRaw) {
        try {
          const tokens = JSON.parse(tokensRaw);
          if (tokens?.access) {
            config.headers.Authorization = `Bearer ${tokens.access}`;
          }
        } catch {
          // Invalid JSON in localStorage, ignore
        }
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 by attempting token refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Skip refresh logic for the token refresh endpoint itself
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/auth/token/refresh/")
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const tokensRaw = localStorage.getItem("auth-tokens");
        if (!tokensRaw) throw new Error("No tokens available");

        const tokens = JSON.parse(tokensRaw);
        if (!tokens?.refresh) throw new Error("No refresh token");

        const response = await axios.post("/api/auth/token/refresh/", {
          refresh: tokens.refresh,
        });

        const newAccess = response.data.access;
        const updatedTokens = { ...tokens, access: newAccess };
        localStorage.setItem("auth-tokens", JSON.stringify(updatedTokens));

        processQueue(null, newAccess);
        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        // Clear tokens and redirect to login on refresh failure
        localStorage.removeItem("auth-tokens");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
