import api from "@/lib/api";
import {
  RFPDocument,
  RFPRequirement,
  ComplianceMatrixItem,
  Amendment,
} from "@/types/rfp";

export async function getRFPDocuments(
  params?: Record<string, string>
): Promise<{ results: RFPDocument[]; count: number }> {
  const response = await api.get("/rfp/documents/", { params });
  return response.data;
}

export async function getRFPDocument(id: string): Promise<RFPDocument> {
  const response = await api.get(`/rfp/documents/${id}/`);
  return response.data;
}

export async function createRFPDocument(data: {
  deal: string;
  title: string;
  document_type: string;
  file_url?: string;
}): Promise<RFPDocument> {
  const response = await api.post("/rfp/documents/", data);
  return response.data;
}

export async function getRFPRequirements(
  documentId: string
): Promise<{ results: RFPRequirement[]; count: number }> {
  const response = await api.get("/rfp/requirements/", {
    params: { document: documentId },
  });
  return response.data;
}

export async function getComplianceMatrix(
  documentId: string
): Promise<{ results: ComplianceMatrixItem[]; count: number }> {
  const response = await api.get("/rfp/compliance-matrix/", {
    params: { document: documentId },
  });
  return response.data;
}

export async function updateComplianceItem(
  id: string,
  data: Partial<ComplianceMatrixItem>
): Promise<ComplianceMatrixItem> {
  const response = await api.patch(`/rfp/compliance-matrix/${id}/`, data);
  return response.data;
}

export async function getAmendments(
  documentId: string
): Promise<{ results: Amendment[]; count: number }> {
  const response = await api.get("/rfp/amendments/", {
    params: { document: documentId },
  });
  return response.data;
}
