import { Namespace, Socket } from "socket.io";

export interface CursorPosition {
  user_id: string;
  user_name: string;
  x: number;
  y: number;
  section?: string;
}

export interface EditOperation {
  user_id: string;
  document_id: string;
  operation_type: string;
  path: string;
  value: unknown;
  revision: number;
  timestamp: string;
}

/**
 * Register collaboration event handlers for live proposal editing.
 *
 * Client events:
 *   - join_document   : Join a document editing room
 *   - leave_document  : Leave a document editing room
 *   - cursor_move     : Broadcast cursor position to other collaborators
 *   - edit_operation   : Broadcast an OT/CRDT operation to other collaborators
 *
 * Server events (broadcast to room):
 *   - user_joined     : A new user joined the document
 *   - user_left       : A user left the document
 *   - cursor_update   : Another user's cursor moved
 *   - remote_edit     : An edit operation from another user
 */
export function registerCollaborationHandlers(
  namespace: Namespace,
  socket: Socket
): void {
  // Join a document editing room
  socket.on(
    "join_document",
    (payload: { document_id: string }, callback?: Function) => {
      const room = `doc:${payload.document_id}`;
      socket.join(room);
      socket.data.currentDocument = payload.document_id;

      console.log(
        `[collaboration] ${socket.data.user?.sub || socket.id} joined document ${payload.document_id}`
      );

      // Notify other users in the room
      socket.to(room).emit("user_joined", {
        user_id: socket.data.user?.sub,
        user_name: socket.data.user?.name || "Anonymous",
        socket_id: socket.id,
        joined_at: new Date().toISOString(),
      });

      if (callback) {
        callback({ status: "joined", document_id: payload.document_id });
      }
    }
  );

  // Leave a document editing room
  socket.on(
    "leave_document",
    (payload: { document_id: string }, callback?: Function) => {
      const room = `doc:${payload.document_id}`;
      socket.leave(room);

      console.log(
        `[collaboration] ${socket.data.user?.sub || socket.id} left document ${payload.document_id}`
      );

      // Notify other users in the room
      socket.to(room).emit("user_left", {
        user_id: socket.data.user?.sub,
        socket_id: socket.id,
        left_at: new Date().toISOString(),
      });

      socket.data.currentDocument = null;

      if (callback) {
        callback({ status: "left", document_id: payload.document_id });
      }
    }
  );

  // Broadcast cursor position to other collaborators
  socket.on("cursor_move", (payload: { x: number; y: number; section?: string }) => {
    const documentId = socket.data.currentDocument;
    if (!documentId) return;

    const room = `doc:${documentId}`;
    const cursorData: CursorPosition = {
      user_id: socket.data.user?.sub || socket.id,
      user_name: socket.data.user?.name || "Anonymous",
      x: payload.x,
      y: payload.y,
      section: payload.section,
    };

    socket.to(room).emit("cursor_update", cursorData);
  });

  // Broadcast OT/CRDT edit operation to other collaborators
  socket.on(
    "edit_operation",
    (
      payload: {
        operation_type: string;
        path: string;
        value: unknown;
        revision: number;
      },
      callback?: Function
    ) => {
      const documentId = socket.data.currentDocument;
      if (!documentId) {
        if (callback) {
          callback({ status: "error", message: "Not in a document room" });
        }
        return;
      }

      const room = `doc:${documentId}`;
      const operation: EditOperation = {
        user_id: socket.data.user?.sub || socket.id,
        document_id: documentId,
        operation_type: payload.operation_type,
        path: payload.path,
        value: payload.value,
        revision: payload.revision,
        timestamp: new Date().toISOString(),
      };

      // Broadcast to all other users in the document room
      socket.to(room).emit("remote_edit", operation);

      if (callback) {
        callback({ status: "ok", revision: payload.revision });
      }
    }
  );

  // Clean up on disconnect: notify rooms the user was in
  socket.on("disconnect", () => {
    const documentId = socket.data.currentDocument;
    if (documentId) {
      const room = `doc:${documentId}`;
      socket.to(room).emit("user_left", {
        user_id: socket.data.user?.sub,
        socket_id: socket.id,
        left_at: new Date().toISOString(),
      });
    }
  });
}
