import api from '@/lib/api';

// ── Types ──────────────────────────────────────────────────

export type InterestLevel = 'strongly_interested' | 'moderately_interested' | 'low_interest' | 'info_only';
export type ResponseStatus = 'draft' | 'in_review' | 'submitted' | 'no_response';

export interface SourcesSoughtResponse {
  id: string;
  deal: string | null;
  deal_name: string;
  opportunity: string | null;
  title: string;
  solicitation_number: string;
  company_overview: string;
  relevant_experience: string;
  technical_approach_summary: string;
  capability_gaps: string;
  questions_for_government: string[];
  interest_level: InterestLevel;
  interest_level_display: string;
  status: ResponseStatus;
  status_display: string;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface SourcesSoughtPayload {
  title: string;
  solicitation_number: string;
  deal_name: string;
  interest_level: InterestLevel;
  status: ResponseStatus;
  company_overview: string;
  relevant_experience: string;
  technical_approach_summary: string;
  capability_gaps: string;
  questions_for_government: string[];
}

// ── API Functions ──────────────────────────────────────────

const BASE = '/proposals/sources-sought';

export async function getSourcesSought(): Promise<SourcesSoughtResponse[]> {
  const res = await api.get(`${BASE}/`);
  return res.data;
}

export async function getSourcesSoughtById(id: string): Promise<SourcesSoughtResponse> {
  const res = await api.get(`${BASE}/${id}/`);
  return res.data;
}

export async function createSourcesSought(data: SourcesSoughtPayload): Promise<SourcesSoughtResponse> {
  const res = await api.post(`${BASE}/`, data);
  return res.data;
}

export async function updateSourcesSought(
  id: string,
  data: Partial<SourcesSoughtPayload>
): Promise<SourcesSoughtResponse> {
  const res = await api.patch(`${BASE}/${id}/`, data);
  return res.data;
}

export async function deleteSourcesSought(id: string): Promise<void> {
  await api.delete(`${BASE}/${id}/`);
}
