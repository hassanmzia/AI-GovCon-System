import { io, Socket } from "socket.io-client";

/**
 * Socket.IO client for the realtime server.
 *
 * Three namespaces:
 *  - /notifications — push notifications, approval alerts, deadline warnings
 *  - /collaboration — concurrent editing, cursors
 *  - /ai-stream     — live agent execution streaming, thinking steps
 *
 * The realtime server is proxied via Nginx at /ws/.
 */

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("auth-tokens");
    if (!raw) return null;
    return JSON.parse(raw)?.access ?? null;
  } catch {
    return null;
  }
}

function createNamespaceSocket(namespace: string): Socket {
  const token = getAccessToken();
  return io(`/ws${namespace}`, {
    path: "/ws/socket.io",
    transports: ["websocket", "polling"],
    auth: { token },
    autoConnect: false,
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 10000,
  });
}

// Lazy singletons — created once, reused across the app.
let _notifications: Socket | null = null;
let _aiStream: Socket | null = null;
let _collaboration: Socket | null = null;

export function getNotificationsSocket(): Socket {
  if (!_notifications) {
    _notifications = createNamespaceSocket("/notifications");
  }
  return _notifications;
}

export function getAiStreamSocket(): Socket {
  if (!_aiStream) {
    _aiStream = createNamespaceSocket("/ai-stream");
  }
  return _aiStream;
}

export function getCollaborationSocket(): Socket {
  if (!_collaboration) {
    _collaboration = createNamespaceSocket("/collaboration");
  }
  return _collaboration;
}

/** Disconnect all sockets (call on logout). */
export function disconnectAll(): void {
  [_notifications, _aiStream, _collaboration].forEach((s) => {
    if (s?.connected) s.disconnect();
  });
  _notifications = null;
  _aiStream = null;
  _collaboration = null;
}
