"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import type { Socket } from "socket.io-client";
import {
  getNotificationsSocket,
  getAiStreamSocket,
  getCollaborationSocket,
} from "@/lib/socket";

type Namespace = "notifications" | "ai-stream" | "collaboration";

const NAMESPACE_GETTERS: Record<Namespace, () => Socket> = {
  notifications: getNotificationsSocket,
  "ai-stream": getAiStreamSocket,
  collaboration: getCollaborationSocket,
};

/**
 * Connect to a Socket.IO namespace and subscribe to events.
 *
 * @param namespace  Which namespace to connect to.
 * @param events     Map of event name → handler. Handlers are auto-cleaned
 *                   up when the component unmounts or the deps change.
 *
 * Returns `{ socket, connected }`.
 */
export function useSocket(
  namespace: Namespace,
  events?: Record<string, (...args: unknown[]) => void>
) {
  const socketRef = useRef<Socket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const socket = NAMESPACE_GETTERS[namespace]();
    socketRef.current = socket;

    const onConnect = () => setConnected(true);
    const onDisconnect = () => setConnected(false);

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);

    // Register event handlers
    if (events) {
      Object.entries(events).forEach(([event, handler]) => {
        socket.on(event, handler);
      });
    }

    if (!socket.connected) {
      socket.connect();
    } else {
      setConnected(true);
    }

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      if (events) {
        Object.entries(events).forEach(([event, handler]) => {
          socket.off(event, handler);
        });
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [namespace]);

  const emit = useCallback(
    (event: string, ...args: unknown[]) => {
      socketRef.current?.emit(event, ...args);
    },
    []
  );

  return { socket: socketRef.current, connected, emit };
}

/**
 * Hook for subscribing to live AI agent execution streams.
 *
 * Provides `agentEvents` array of events received so far and
 * `isStreaming` flag.
 */
export function useAiStream(dealId?: string) {
  const [events, setEvents] = useState<unknown[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const handlers = {
    "agent:started": (data: unknown) => {
      setIsStreaming(true);
      setEvents((prev) => [...prev, { type: "started", ...data as object }]);
    },
    "agent:thinking": (data: unknown) => {
      setEvents((prev) => [...prev, { type: "thinking", ...data as object }]);
    },
    "agent:tool_call": (data: unknown) => {
      setEvents((prev) => [...prev, { type: "tool_call", ...data as object }]);
    },
    "agent:result": (data: unknown) => {
      setEvents((prev) => [...prev, { type: "result", ...data as object }]);
    },
    "agent:completed": (data: unknown) => {
      setIsStreaming(false);
      setEvents((prev) => [...prev, { type: "completed", ...data as object }]);
    },
    "agent:error": (data: unknown) => {
      setIsStreaming(false);
      setEvents((prev) => [...prev, { type: "error", ...data as object }]);
    },
  };

  const { socket, connected, emit } = useSocket("ai-stream", handlers);

  // Subscribe to deal-specific stream when dealId changes
  useEffect(() => {
    if (connected && dealId) {
      socket?.emit("subscribe:deal", { deal_id: dealId });
      return () => {
        socket?.emit("unsubscribe:deal", { deal_id: dealId });
      };
    }
  }, [connected, dealId, socket]);

  const clearEvents = useCallback(() => setEvents([]), []);

  return { events, isStreaming, connected, emit, clearEvents };
}

/**
 * Hook for live notifications via WebSocket.
 */
export function useRealtimeNotifications(
  onNotification?: (data: unknown) => void
) {
  const handlers = {
    notification: (data: unknown) => {
      onNotification?.(data);
    },
    "approval:requested": (data: unknown) => {
      onNotification?.(data);
    },
    "deal:stage_changed": (data: unknown) => {
      onNotification?.(data);
    },
    "deadline:warning": (data: unknown) => {
      onNotification?.(data);
    },
  };

  return useSocket("notifications", handlers);
}
