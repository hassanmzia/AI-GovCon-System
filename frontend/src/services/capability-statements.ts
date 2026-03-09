import api from "@/lib/api";

// ── Types ────────────────────────────────────────────────────

export interface PastPerformanceEntry {
  id?: string;
  projectName: string;
  agency: string;
  summary: string;
}

export interface ContactInfo {
  name: string;
  title: string;
  email: string;
  phone: string;
  website: string;
}

export interface CompanyData {
  uei: string;
  cageCode: string;
  naicsCodes: string[];
  pscCodes: string[];
  certifications: string[];
  contractVehicles: string[];
}

export interface CapabilityStatement {
  id: string;
  company_profile: string | null;
  company_name: string;
  title: string;
  version: number;
  is_primary: boolean;
  company_overview: string;
  core_competencies: string[];
  differentiators: string[];
  past_performance_highlights: PastPerformanceEntry[];
  duns_number: string;
  uei_number: string;
  cage_code: string;
  naics_codes: string[];
  psc_codes: string[];
  certifications: string[];
  contract_vehicles: string[];
  contact_name: string;
  contact_title: string;
  contact_email: string;
  contact_phone: string;
  website: string;
  target_agency: string;
  target_naics: string;
  created_at: string;
  updated_at: string;
}

export interface CapabilityStatementListItem {
  id: string;
  company_profile: string | null;
  company_name: string;
  title: string;
  version: number;
  is_primary: boolean;
  target_agency: string;
  target_naics: string;
  created_at: string;
  updated_at: string;
}

export interface CapabilityStatementPayload {
  company_profile?: string | null;
  title?: string;
  version?: number;
  is_primary?: boolean;
  company_overview?: string;
  core_competencies?: string[];
  differentiators?: string[];
  past_performance_highlights?: PastPerformanceEntry[];
  duns_number?: string;
  uei_number?: string;
  cage_code?: string;
  naics_codes?: string[];
  psc_codes?: string[];
  certifications?: string[];
  contract_vehicles?: string[];
  contact_name?: string;
  contact_title?: string;
  contact_email?: string;
  contact_phone?: string;
  website?: string;
  target_agency?: string;
  target_naics?: string;
}

export interface AIImprovementResult {
  suggestions?: Array<{ section: string; suggestion: string }>;
  improved_sections?: Record<string, string | string[]>;
  quality_score?: number;
  summary?: string;
  error?: string;
  fallback_tips?: string[];
}

// ── API ──────────────────────────────────────────────────────

export async function getCapabilityStatements(
  params?: Record<string, string>
): Promise<{ results: CapabilityStatementListItem[]; count: number }> {
  const response = await api.get("/marketing/capability-statements/", {
    params,
  });
  return response.data;
}

export async function getCapabilityStatement(
  id: string
): Promise<CapabilityStatement> {
  const response = await api.get(`/marketing/capability-statements/${id}/`);
  return response.data;
}

export async function createCapabilityStatement(
  payload: CapabilityStatementPayload
): Promise<CapabilityStatement> {
  const response = await api.post(
    "/marketing/capability-statements/",
    payload
  );
  return response.data;
}

export async function updateCapabilityStatement(
  id: string,
  payload: Partial<CapabilityStatementPayload>
): Promise<CapabilityStatement> {
  const response = await api.patch(
    `/marketing/capability-statements/${id}/`,
    payload
  );
  return response.data;
}

export async function deleteCapabilityStatement(
  id: string
): Promise<void> {
  await api.delete(`/marketing/capability-statements/${id}/`);
}

export async function setPrimary(
  id: string
): Promise<CapabilityStatement> {
  const response = await api.post(
    `/marketing/capability-statements/${id}/set-primary/`
  );
  return response.data;
}

export async function unsetPrimary(
  id: string
): Promise<CapabilityStatement> {
  const response = await api.post(
    `/marketing/capability-statements/${id}/unset-primary/`
  );
  return response.data;
}

export async function duplicateStatement(
  id: string
): Promise<CapabilityStatement> {
  const response = await api.post(
    `/marketing/capability-statements/${id}/duplicate/`
  );
  return response.data;
}

export async function aiImprove(
  id: string,
  focus: string = "all"
): Promise<AIImprovementResult> {
  const response = await api.post(
    `/marketing/capability-statements/${id}/ai-improve/`,
    { focus }
  );
  return response.data;
}
