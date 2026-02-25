import { Namespace, Socket } from "socket.io";

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: "info" | "warning" | "success" | "error";
  entity: {
    type: string;
    id: string;
  };
  created_at: string;
}

/**
 * Register notification event handlers for a connected socket.
 *
 * Client events:
 *   - subscribe   : Join a room by deal_id or user_id to receive targeted notifications
 *   - mark_read   : Mark a notification as read; emits acknowledgment back
 *
 * Server events (emitted to rooms):
 *   - notification : Pushes a new notification (title, message, type, entity)
 */
export function registerNotificationHandlers(
  namespace: Namespace,
  socket: Socket
): void {
  // Automatically join user-specific room
  const userId = socket.data.user?.sub;
  if (userId) {
    socket.join(`user:${userId}`);
  }

  // Subscribe to a room by deal_id or user_id
  socket.on(
    "subscribe",
    (payload: { deal_id?: string; user_id?: string }, callback?: Function) => {
      if (payload.deal_id) {
        const room = `deal:${payload.deal_id}`;
        socket.join(room);
        console.log(`[notifications] ${socket.id} joined room ${room}`);
      }

      if (payload.user_id) {
        const room = `user:${payload.user_id}`;
        socket.join(room);
        console.log(`[notifications] ${socket.id} joined room ${room}`);
      }

      if (callback) {
        callback({ status: "subscribed" });
      }
    }
  );

  // Mark a notification as read
  socket.on(
    "mark_read",
    (payload: { notification_id: string }, callback?: Function) => {
      console.log(
        `[notifications] ${socket.id} marked notification ${payload.notification_id} as read`
      );

      // Acknowledge back to the sender
      socket.emit("notification_read", {
        notification_id: payload.notification_id,
        read_at: new Date().toISOString(),
      });

      if (callback) {
        callback({ status: "ok", notification_id: payload.notification_id });
      }
    }
  );
}

/**
 * Utility: emit a notification to a specific room from the server side.
 */
export function emitNotification(
  namespace: Namespace,
  room: string,
  notification: Notification
): void {
  namespace.to(room).emit("notification", notification);
}
