import api from "@/lib/api";
import {
  FARClause,
  RegulatoryRequirement,
  ComplianceAssessment,
  LegalRisk,
  ContractReviewNote,
} from "@/types/legal";

export async function getFARClauses(
  params?: Record<string, string>
): Promise<{ results: FARClause[]; count: number }> {
  const response = await api.get("/legal/far-clauses/", { params });
  return response.data;
}

export async function getFARClause(id: string): Promise<FARClause> {
  const response = await api.get(`/legal/far-clauses/${id}/`);
  return response.data;
}

export async function getRegulatoryRequirements(
  params?: Record<string, string>
): Promise<{ results: RegulatoryRequirement[]; count: number }> {
  const response = await api.get("/legal/regulatory-requirements/", { params });
  return response.data;
}

export async function getComplianceAssessments(
  params?: Record<string, string>
): Promise<{ results: ComplianceAssessment[]; count: number }> {
  const response = await api.get("/legal/compliance-assessments/", { params });
  return response.data;
}

export async function getLegalRisks(
  params?: Record<string, string>
): Promise<{ results: LegalRisk[]; count: number }> {
  const response = await api.get("/legal/legal-risks/", { params });
  return response.data;
}

export async function getContractReviewNotes(
  params?: Record<string, string>
): Promise<{ results: ContractReviewNote[]; count: number }> {
  const response = await api.get("/legal/contract-review-notes/", { params });
  return response.data;
}
