import api from "@/lib/api";
import { TeamingPartnership, TeamingPartner, TeamingAgreement } from "@/types/teaming";

export async function getPartnerships(
  params?: Record<string, string>
): Promise<{ results: TeamingPartnership[]; count: number }> {
  const response = await api.get("/teaming/partnerships/", { params });
  return response.data;
}

export async function getPartnership(id: string): Promise<TeamingPartnership> {
  const response = await api.get(`/teaming/partnerships/${id}/`);
  return response.data;
}

export async function createPartnership(
  data: Partial<TeamingPartnership>
): Promise<TeamingPartnership> {
  const response = await api.post("/teaming/partnerships/", data);
  return response.data;
}

export async function updatePartnership(
  id: string,
  data: Partial<TeamingPartnership>
): Promise<TeamingPartnership> {
  const response = await api.patch(`/teaming/partnerships/${id}/`, data);
  return response.data;
}

export async function deletePartnership(id: string): Promise<void> {
  await api.delete(`/teaming/partnerships/${id}/`);
}

// ── Partner Directory ──

export async function getPartners(
  params?: Record<string, string>
): Promise<{ results: TeamingPartner[]; count: number }> {
  const response = await api.get("/teaming/partners/", { params });
  return response.data;
}

export async function getPartner(id: string): Promise<TeamingPartner> {
  const response = await api.get(`/teaming/partners/${id}/`);
  return response.data;
}

export async function createPartner(data: Partial<TeamingPartner>): Promise<TeamingPartner> {
  const response = await api.post("/teaming/partners/", data);
  return response.data;
}

export async function updatePartner(id: string, data: Partial<TeamingPartner>): Promise<TeamingPartner> {
  const response = await api.patch(`/teaming/partners/${id}/`, data);
  return response.data;
}

export async function deletePartner(id: string): Promise<void> {
  await api.delete(`/teaming/partners/${id}/`);
}

export async function getPartnerRiskAssessment(id: string): Promise<Record<string, unknown>> {
  const response = await api.get(`/teaming/partners/${id}/risk_assessment/`);
  return response.data;
}

export async function searchPartnersByCapability(
  query: string,
  filters?: { naics_codes?: string[]; clearance_level?: string; sb_certifications?: string[] }
): Promise<{ results: Record<string, unknown>[]; count: number }> {
  const response = await api.post("/teaming/partners/search_by_capability/", {
    query,
    ...filters,
  });
  return response.data;
}

export async function optimizeTeam(data: {
  opportunity: Record<string, unknown>;
  partner_ids: string[];
  required_capabilities: string[];
  max_partners?: number;
}): Promise<Record<string, unknown>> {
  const response = await api.post("/teaming/partners/optimize_team/", data);
  return response.data;
}

export async function checkSbCompliance(data: {
  team_members: Record<string, unknown>[];
  opportunity: Record<string, unknown>;
  sb_goals?: Record<string, number>;
}): Promise<Record<string, unknown>> {
  const response = await api.post("/teaming/partners/sb_compliance/", data);
  return response.data;
}

// ── Agreements ──

export async function getAgreements(
  params?: Record<string, string>
): Promise<{ results: TeamingAgreement[]; count: number }> {
  const response = await api.get("/teaming/agreements/", { params });
  return response.data;
}

export async function getAgreement(id: string): Promise<TeamingAgreement> {
  const response = await api.get(`/teaming/agreements/${id}/`);
  return response.data;
}

export async function createAgreement(data: Partial<TeamingAgreement>): Promise<TeamingAgreement> {
  const response = await api.post("/teaming/agreements/", data);
  return response.data;
}

export async function updateAgreement(id: string, data: Partial<TeamingAgreement>): Promise<TeamingAgreement> {
  const response = await api.patch(`/teaming/agreements/${id}/`, data);
  return response.data;
}

export async function deleteAgreement(id: string): Promise<void> {
  await api.delete(`/teaming/agreements/${id}/`);
}

export async function generateAgreementDocument(
  id: string,
  primeName: string
): Promise<Record<string, unknown>> {
  const response = await api.post(`/teaming/agreements/${id}/generate_document/`, {
    prime_name: primeName,
  });
  return response.data;
}

export async function markAgreementSigned(
  id: string,
  data: { signed_date?: string; our_signatory?: string; partner_signatory?: string }
): Promise<TeamingAgreement> {
  const response = await api.post(`/teaming/agreements/${id}/mark_signed/`, data);
  return response.data;
}
