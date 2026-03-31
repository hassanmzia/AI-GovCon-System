import api from "@/lib/api";
import { DocumentTemplate } from "@/types/template";

export async function getTemplates(
  params?: Record<string, string>
): Promise<{ results: DocumentTemplate[]; count: number }> {
  const response = await api.get("/knowledge-vault/templates/", { params });
  return response.data;
}

export async function getTemplate(id: string): Promise<DocumentTemplate> {
  const response = await api.get(`/knowledge-vault/templates/${id}/`);
  return response.data;
}

export async function createTemplate(data: FormData): Promise<DocumentTemplate> {
  const response = await api.post("/knowledge-vault/templates/", data, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function updateTemplate(
  id: string,
  data: FormData | Partial<DocumentTemplate>
): Promise<DocumentTemplate> {
  const isFormData = data instanceof FormData;
  const response = await api.patch(`/knowledge-vault/templates/${id}/`, data, {
    headers: isFormData ? { "Content-Type": "multipart/form-data" } : undefined,
  });
  return response.data;
}

export async function deleteTemplate(id: string): Promise<void> {
  await api.delete(`/knowledge-vault/templates/${id}/`);
}

export async function setDefaultTemplate(id: string): Promise<void> {
  await api.post(`/knowledge-vault/templates/${id}/set_default/`);
}

export async function duplicateTemplate(
  id: string,
  version?: string
): Promise<DocumentTemplate> {
  const response = await api.post(`/knowledge-vault/templates/${id}/duplicate/`, {
    version,
  });
  return response.data;
}

export async function trackDownload(id: string): Promise<{ usage_count: number }> {
  const response = await api.post(`/knowledge-vault/templates/${id}/track_download/`);
  return response.data;
}

export async function downloadTemplate(id: string): Promise<void> {
  const response = await api.get(`/knowledge-vault/templates/${id}/download/`, {
    responseType: "blob",
  });
  // Extract filename from Content-Disposition header or fall back
  const disposition = response.headers["content-disposition"] || "";
  const match = disposition.match(/filename="?(.+?)"?$/);
  const filename = match ? match[1] : `template-${id}`;

  const url = window.URL.createObjectURL(response.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function renderTemplate(
  id: string,
  variables: Record<string, string>
): Promise<Blob> {
  const response = await api.post(
    `/knowledge-vault/templates/${id}/render/`,
    { variables },
    { responseType: "blob" }
  );
  return response.data;
}

export async function extractVariables(
  id: string
): Promise<{ variables: Array<{ name: string; label: string; default: string }> }> {
  const response = await api.get(
    `/knowledge-vault/templates/${id}/extract_variables/`
  );
  return response.data;
}
