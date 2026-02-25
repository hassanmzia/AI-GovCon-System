import { Namespace, Socket } from "socket.io";

export interface AgentEvent {
  agent_name: string;
  event_type: "thinking" | "tool_call" | "tool_result" | "output" | "error" | "progress";
  data: unknown;
  timestamp: string;
}

export interface AgentComplete {
  agent_name: string;
  execution_id: string;
  status: "success" | "error" | "cancelled";
  result?: unknown;
  duration_ms?: number;
  timestamp: string;
}

/**
 * Register AI streaming event handlers for agent execution monitoring.
 *
 * Client events:
 *   - subscribe_agent : Join an agent execution room to receive streaming updates
 *   - unsubscribe_agent : Leave an agent execution room
 *
 * Server events (emitted to rooms):
 *   - agent_event    : Streaming event from an agent (agent_name, event_type, data)
 *   - agent_complete : Agent execution finished
 */
export function registerAiStreamHandlers(
  namespace: Namespace,
  socket: Socket
): void {
  // Subscribe to an agent execution room
  socket.on(
    "subscribe_agent",
    (payload: { execution_id: string; agent_name?: string }, callback?: Function) => {
      const room = `agent:${payload.execution_id}`;
      socket.join(room);

      console.log(
        `[ai-stream] ${socket.data.user?.sub || socket.id} subscribed to agent execution ${payload.execution_id}`
      );

      if (callback) {
        callback({
          status: "subscribed",
          execution_id: payload.execution_id,
          agent_name: payload.agent_name,
        });
      }
    }
  );

  // Unsubscribe from an agent execution room
  socket.on(
    "unsubscribe_agent",
    (payload: { execution_id: string }, callback?: Function) => {
      const room = `agent:${payload.execution_id}`;
      socket.leave(room);

      console.log(
        `[ai-stream] ${socket.data.user?.sub || socket.id} unsubscribed from agent execution ${payload.execution_id}`
      );

      if (callback) {
        callback({
          status: "unsubscribed",
          execution_id: payload.execution_id,
        });
      }
    }
  );
}

/**
 * Utility: emit an agent event to all subscribers of a given execution.
 */
export function emitAgentEvent(
  namespace: Namespace,
  executionId: string,
  event: AgentEvent
): void {
  const room = `agent:${executionId}`;
  namespace.to(room).emit("agent_event", event);
}

/**
 * Utility: emit an agent completion event to all subscribers of a given execution.
 */
export function emitAgentComplete(
  namespace: Namespace,
  executionId: string,
  completion: AgentComplete
): void {
  const room = `agent:${executionId}`;
  namespace.to(room).emit("agent_complete", completion);
}
