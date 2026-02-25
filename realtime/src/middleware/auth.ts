import { Socket } from "socket.io";
import jwt from "jsonwebtoken";

const JWT_SECRET_KEY = process.env.JWT_SECRET_KEY || "development-secret-key";

export interface AuthenticatedUser {
  sub: string;
  email?: string;
  name?: string;
  role?: string;
  org_id?: string;
  [key: string]: unknown;
}

/**
 * JWT verification middleware for Socket.IO.
 *
 * Extracts the token from:
 *   1. socket.handshake.auth.token
 *   2. socket.handshake.query.token (fallback)
 *
 * On success, attaches the decoded user payload to socket.data.user.
 * On failure, calls next() with an authentication error.
 */
export function authMiddleware(
  socket: Socket,
  next: (err?: Error) => void
): void {
  const token =
    (socket.handshake.auth?.token as string) ||
    (socket.handshake.query?.token as string);

  if (!token) {
    return next(new Error("Authentication error: No token provided"));
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET_KEY) as AuthenticatedUser;
    socket.data.user = decoded;
    next();
  } catch (err) {
    console.error(
      `[auth] JWT verification failed for socket ${socket.id}:`,
      err instanceof Error ? err.message : err
    );
    next(new Error("Authentication error: Invalid or expired token"));
  }
}
