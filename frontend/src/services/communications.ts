import api from "@/lib/api";
import {
  CommunicationThread,
  Message,
  ClarificationQuestion,
} from "@/types/communications";

export async function getThreads(
  params?: Record<string, string>
): Promise<{ results: CommunicationThread[]; count: number }> {
  const response = await api.get("/communications/threads/", { params });
  return response.data;
}

export async function getThread(id: string): Promise<CommunicationThread> {
  const response = await api.get(`/communications/threads/${id}/`);
  return response.data;
}

export async function createThread(
  data: Partial<CommunicationThread>
): Promise<CommunicationThread> {
  const response = await api.post("/communications/threads/", data);
  return response.data;
}

export async function getMessages(
  threadId: string
): Promise<{ results: Message[]; count: number }> {
  const response = await api.get("/communications/messages/", {
    params: { thread: threadId },
  });
  return response.data;
}

export async function sendMessage(data: {
  thread: string;
  content: string;
  message_type?: string;
}): Promise<Message> {
  const response = await api.post("/communications/messages/", data);
  return response.data;
}

export async function getClarificationQuestions(
  params?: Record<string, string>
): Promise<{ results: ClarificationQuestion[]; count: number }> {
  const response = await api.get("/communications/questions/", { params });
  return response.data;
}

export async function createClarificationQuestion(
  data: Partial<ClarificationQuestion>
): Promise<ClarificationQuestion> {
  const response = await api.post("/communications/questions/", data);
  return response.data;
}
