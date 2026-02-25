/**
 * Tests for the auth Zustand store.
 * We mock the api module to avoid real HTTP calls.
 */
import { renderHook, act } from "@testing-library/react";

// Mock the api module before importing the store
jest.mock("@/lib/api", () => ({
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

import api from "@/lib/api";
import { useAuthStore } from "@/store/auth";

const mockApi = api as jest.Mocked<typeof api>;

// Reset store state between tests
beforeEach(() => {
  useAuthStore.setState({
    user: null,
    tokens: null,
    isAuthenticated: false,
  });
  jest.clearAllMocks();
  // Clear localStorage
  localStorage.clear();
});

describe("useAuthStore – login", () => {
  it("sets tokens and isAuthenticated on successful login", async () => {
    mockApi.post.mockResolvedValueOnce({
      data: { access: "access-token", refresh: "refresh-token" },
    });
    mockApi.get.mockResolvedValueOnce({
      data: { id: 1, username: "testuser", email: "t@example.com", role: "capture_manager" },
    });

    const { result } = renderHook(() => useAuthStore());

    await act(async () => {
      await result.current.login("testuser", "Pass123!");
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.tokens?.access).toBe("access-token");
    expect(result.current.user?.username).toBe("testuser");
    expect(localStorage.getItem("auth-tokens")).toContain("access-token");
  });

  it("stores tokens in localStorage on login", async () => {
    mockApi.post.mockResolvedValueOnce({
      data: { access: "acc", refresh: "ref" },
    });
    mockApi.get.mockResolvedValueOnce({ data: { id: 1, username: "u" } });

    const { result } = renderHook(() => useAuthStore());
    await act(async () => {
      await result.current.login("u", "p");
    });

    const stored = JSON.parse(localStorage.getItem("auth-tokens") ?? "null");
    expect(stored?.access).toBe("acc");
    expect(stored?.refresh).toBe("ref");
  });

  it("throws on login failure", async () => {
    mockApi.post.mockRejectedValueOnce(new Error("Invalid credentials"));

    const { result } = renderHook(() => useAuthStore());

    await expect(
      act(async () => {
        await result.current.login("bad", "creds");
      })
    ).rejects.toThrow();
  });
});

describe("useAuthStore – logout", () => {
  it("clears state and localStorage on logout", () => {
    useAuthStore.setState({
      user: { id: 1, username: "u", email: "u@example.com", first_name: "", last_name: "" },
      tokens: { access: "acc", refresh: "ref" },
      isAuthenticated: true,
    });
    localStorage.setItem("auth-tokens", JSON.stringify({ access: "acc", refresh: "ref" }));

    // Mock window.location.href setter
    const originalLocation = window.location;
    // @ts-ignore
    delete window.location;
    // @ts-ignore
    window.location = { href: "" };

    const { result } = renderHook(() => useAuthStore());
    act(() => {
      result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.tokens).toBeNull();
    expect(localStorage.getItem("auth-tokens")).toBeNull();

    // Restore
    window.location = originalLocation;
  });
});

describe("useAuthStore – refreshToken", () => {
  it("updates access token while preserving refresh token", async () => {
    useAuthStore.setState({
      tokens: { access: "old-access", refresh: "my-refresh" },
      isAuthenticated: true,
    });

    mockApi.post.mockResolvedValueOnce({ data: { access: "new-access" } });

    const { result } = renderHook(() => useAuthStore());
    await act(async () => {
      await result.current.refreshToken();
    });

    expect(result.current.tokens?.access).toBe("new-access");
    expect(result.current.tokens?.refresh).toBe("my-refresh");
  });

  it("throws when no refresh token available", async () => {
    const { result } = renderHook(() => useAuthStore());

    await expect(
      act(async () => {
        await result.current.refreshToken();
      })
    ).rejects.toThrow("No refresh token available");
  });
});

describe("useAuthStore – setUser", () => {
  it("updates the user in state", () => {
    const { result } = renderHook(() => useAuthStore());
    const user = {
      id: 42, username: "newuser", email: "new@example.com",
      first_name: "New", last_name: "User",
    };
    act(() => {
      result.current.setUser(user);
    });
    expect(result.current.user?.id).toBe(42);
    expect(result.current.user?.username).toBe("newuser");
  });
});

describe("useAuthStore – initialize", () => {
  it("reads tokens from localStorage and fetches /auth/me/", async () => {
    const tokens = { access: "stored-access", refresh: "stored-refresh" };
    localStorage.setItem("auth-tokens", JSON.stringify(tokens));

    mockApi.get.mockResolvedValueOnce({
      data: { id: 5, username: "stored_user", email: "s@example.com" },
    });

    const { result } = renderHook(() => useAuthStore());
    await act(async () => {
      await result.current.initialize();
    });

    expect(result.current.tokens?.access).toBe("stored-access");
    expect(result.current.user?.username).toBe("stored_user");
    expect(result.current.isAuthenticated).toBe(true);
  });

  it("does nothing when localStorage is empty", async () => {
    const { result } = renderHook(() => useAuthStore());
    await act(async () => {
      await result.current.initialize();
    });
    expect(result.current.isAuthenticated).toBe(false);
    expect(mockApi.get).not.toHaveBeenCalled();
  });
});
