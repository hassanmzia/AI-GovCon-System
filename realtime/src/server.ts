import express from "express";
import { createServer } from "http";
import { Server } from "socket.io";
import cors from "cors";
import { createAdapter } from "@socket.io/redis-adapter";
import Redis from "ioredis";
import { authMiddleware } from "./middleware/auth";
import { registerNotificationHandlers } from "./handlers/notifications";
import { registerCollaborationHandlers } from "./handlers/collaboration";
import { registerAiStreamHandlers } from "./handlers/ai-stream";

const PORT = parseInt(process.env.PORT || "8002", 10);
const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";

const app = express();
app.use(cors());

// Health check endpoint
app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "realtime" });
});

const httpServer = createServer(app);

const io = new Server(httpServer, {
  cors: {
    origin: process.env.CORS_ORIGINS?.split(",") || ["http://localhost:3027"],
    methods: ["GET", "POST"],
    credentials: true,
  },
  transports: ["websocket", "polling"],
});

// ── Redis Adapter for Pub/Sub Across Instances ──────────────────────────────

async function setupRedisAdapter(): Promise<void> {
  try {
    const pubClient = new Redis(REDIS_URL);
    const subClient = pubClient.duplicate();

    await Promise.all([
      new Promise<void>((resolve) => pubClient.on("ready", resolve)),
      new Promise<void>((resolve) => subClient.on("ready", resolve)),
    ]);

    io.adapter(createAdapter(pubClient, subClient) as any);
    console.log("[realtime] Redis adapter connected for pub/sub");
  } catch (err) {
    console.warn(
      "[realtime] Redis adapter unavailable, running in single-instance mode:",
      err
    );
  }
}

// ── Namespace: /notifications ───────────────────────────────────────────────

const notificationsNs = io.of("/notifications");
notificationsNs.use(authMiddleware);
notificationsNs.on("connection", (socket) => {
  console.log(
    `[notifications] User connected: ${socket.data.user?.sub || "unknown"} (${socket.id})`
  );
  registerNotificationHandlers(notificationsNs, socket);

  socket.on("disconnect", (reason) => {
    console.log(
      `[notifications] User disconnected: ${socket.data.user?.sub || "unknown"} (${reason})`
    );
  });
});

// ── Namespace: /collaboration ───────────────────────────────────────────────

const collaborationNs = io.of("/collaboration");
collaborationNs.use(authMiddleware);
collaborationNs.on("connection", (socket) => {
  console.log(
    `[collaboration] User connected: ${socket.data.user?.sub || "unknown"} (${socket.id})`
  );
  registerCollaborationHandlers(collaborationNs, socket);

  socket.on("disconnect", (reason) => {
    console.log(
      `[collaboration] User disconnected: ${socket.data.user?.sub || "unknown"} (${reason})`
    );
  });
});

// ── Namespace: /ai-stream ───────────────────────────────────────────────────

const aiStreamNs = io.of("/ai-stream");
aiStreamNs.use(authMiddleware);
aiStreamNs.on("connection", (socket) => {
  console.log(
    `[ai-stream] User connected: ${socket.data.user?.sub || "unknown"} (${socket.id})`
  );
  registerAiStreamHandlers(aiStreamNs, socket);

  socket.on("disconnect", (reason) => {
    console.log(
      `[ai-stream] User disconnected: ${socket.data.user?.sub || "unknown"} (${reason})`
    );
  });
});

// ── Start Server ────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  await setupRedisAdapter();

  httpServer.listen(PORT, () => {
    console.log(`[realtime] Server listening on port ${PORT}`);
    console.log(`[realtime] Namespaces: /notifications, /collaboration, /ai-stream`);
  });
}

main().catch((err) => {
  console.error("[realtime] Failed to start server:", err);
  process.exit(1);
});
