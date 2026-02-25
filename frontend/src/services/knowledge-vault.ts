import api from "@/lib/api";
import { KnowledgeDocument } from "@/types/knowledge-vault";

export async function getDocuments(
  params?: Record<string, string>
): Promise<{ results: KnowledgeDocument[]; count: number }> {
  const response = await api.get("/knowledge-vault/documents/", { params });
  return response.data;
}

export async function getDocument(id: string): Promise<KnowledgeDocument> {
  const response = await api.get(`/knowledge-vault/documents/${id}/`);
  return response.data;
}

export async function uploadDocument(
  data: FormData
): Promise<KnowledgeDocument> {
  const response = await api.post("/knowledge-vault/documents/", data, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function updateDocument(
  id: string,
  data: Partial<KnowledgeDocument>
): Promise<KnowledgeDocument> {
  const response = await api.patch(`/knowledge-vault/documents/${id}/`, data);
  return response.data;
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/knowledge-vault/documents/${id}/`);
}
