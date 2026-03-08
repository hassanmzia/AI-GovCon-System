/**
 * Tests for the socket module (lib/socket.ts).
 * We mock socket.io-client to avoid real WebSocket connections.
 */

const mockSocket = {
  connected: false,
  connect: jest.fn(),
  disconnect: jest.fn(),
  on: jest.fn(),
  off: jest.fn(),
  emit: jest.fn(),
};

jest.mock("socket.io-client", () => ({
  io: jest.fn(() => ({ ...mockSocket })),
  Socket: jest.fn(),
}));

import { io } from "socket.io-client";
import {
  getNotificationsSocket,
  getAiStreamSocket,
  getCollaborationSocket,
  disconnectAll,
} from "@/lib/socket";

const mockIo = io as jest.MockedFunction<typeof io>;

beforeEach(() => {
  // Reset the singletons by calling disconnectAll
  disconnectAll();
  jest.clearAllMocks();

  // Re-configure mockIo to return fresh socket-like objects
  mockIo.mockImplementation(() => ({
    ...mockSocket,
    connected: false,
  }) as any);
});

describe("getNotificationsSocket", () => {
  it("returns a socket instance", () => {
    const socket = getNotificationsSocket();
    expect(socket).toBeDefined();
    expect(mockIo).toHaveBeenCalledWith(
      "/ws/notifications",
      expect.objectContaining({
        path: "/ws/socket.io",
        transports: ["websocket", "polling"],
        autoConnect: false,
      })
    );
  });

  it("reuses the same singleton on subsequent calls", () => {
    const first = getNotificationsSocket();
    const second = getNotificationsSocket();

    expect(first).toBe(second);
    expect(mockIo).toHaveBeenCalledTimes(1);
  });
});

describe("getAiStreamSocket", () => {
  it("returns a socket instance", () => {
    const socket = getAiStreamSocket();
    expect(socket).toBeDefined();
    expect(mockIo).toHaveBeenCalledWith(
      "/ws/ai-stream",
      expect.objectContaining({
        path: "/ws/socket.io",
        autoConnect: false,
        reconnection: true,
      })
    );
  });

  it("reuses the same singleton on subsequent calls", () => {
    const first = getAiStreamSocket();
    const second = getAiStreamSocket();

    expect(first).toBe(second);
    expect(mockIo).toHaveBeenCalledTimes(1);
  });
});

describe("getCollaborationSocket", () => {
  it("returns a socket instance", () => {
    const socket = getCollaborationSocket();
    expect(socket).toBeDefined();
    expect(mockIo).toHaveBeenCalledWith(
      "/ws/collaboration",
      expect.objectContaining({
        path: "/ws/socket.io",
      })
    );
  });

  it("reuses the same singleton on subsequent calls", () => {
    const first = getCollaborationSocket();
    const second = getCollaborationSocket();

    expect(first).toBe(second);
    expect(mockIo).toHaveBeenCalledTimes(1);
  });
});

describe("disconnectAll", () => {
  it("disconnects all connected sockets", () => {
    // Create sockets that appear connected
    const connectedSocket = { ...mockSocket, connected: true, disconnect: jest.fn() };
    mockIo
      .mockReturnValueOnce(connectedSocket as any)
      .mockReturnValueOnce(connectedSocket as any)
      .mockReturnValueOnce(connectedSocket as any);

    getNotificationsSocket();
    getAiStreamSocket();
    getCollaborationSocket();

    disconnectAll();

    // disconnect should be called for each connected socket
    expect(connectedSocket.disconnect).toHaveBeenCalledTimes(3);
  });

  it("does not call disconnect on sockets that are not connected", () => {
    const disconnectedSocket = { ...mockSocket, connected: false, disconnect: jest.fn() };
    mockIo.mockReturnValue(disconnectedSocket as any);

    getNotificationsSocket();
    getAiStreamSocket();

    disconnectAll();

    expect(disconnectedSocket.disconnect).not.toHaveBeenCalled();
  });

  it("clears singletons so new sockets are created on next call", () => {
    getNotificationsSocket();
    expect(mockIo).toHaveBeenCalledTimes(1);

    disconnectAll();

    getNotificationsSocket();
    // A new socket should be created since singletons were cleared
    expect(mockIo).toHaveBeenCalledTimes(2);
  });
});

describe("socket auth token", () => {
  it("passes access token from localStorage to socket auth", () => {
    localStorage.setItem(
      "auth-tokens",
      JSON.stringify({ access: "my-jwt-token", refresh: "ref" })
    );

    getNotificationsSocket();

    expect(mockIo).toHaveBeenCalledWith(
      "/ws/notifications",
      expect.objectContaining({
        auth: { token: "my-jwt-token" },
      })
    );

    localStorage.clear();
  });

  it("passes null token when localStorage is empty", () => {
    localStorage.clear();

    getNotificationsSocket();

    expect(mockIo).toHaveBeenCalledWith(
      "/ws/notifications",
      expect.objectContaining({
        auth: { token: null },
      })
    );
  });
});
