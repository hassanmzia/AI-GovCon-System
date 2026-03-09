import api from '@/lib/api';

// ── Types ──────────────────────────────────────────────────

export type CertType = 'sb' | 'sdb' | '8a' | 'wosb' | 'edwosb' | 'vosb' | 'sdvosb' | 'hubzone';

export type CertStatus =
  | 'not_applicable'
  | 'eligible'
  | 'in_progress'
  | 'applied'
  | 'under_review'
  | 'certified'
  | 'expired'
  | 'denied';

export interface ApplicationStep {
  name: string;
  completed: boolean;
  notes: string;
}

export interface SBACertification {
  id: string;
  cert_type: CertType;
  cert_type_display: string;
  status: CertStatus;
  status_display: string;
  certification_number: string;
  application_date: string | null;
  certification_date: string | null;
  expiration_date: string | null;
  renewal_date: string | null;
  application_steps: ApplicationStep[];
  documents_uploaded: string[];
  description: string;
  requirements: string;
  notes: string;
  days_until_expiration: number | null;
  created_at: string;
  updated_at: string;
}

export interface NAICSCode {
  id: string;
  code: string;
  title: string;
  size_standard: string;
  is_primary: boolean;
  qualifies_small: boolean;
  created_at: string;
  updated_at: string;
}

export interface CertSummary {
  total: number;
  certified: number;
  in_progress: number;
  eligible: number;
}

// ── API Functions ──────────────────────────────────────────

const BASE = '/sba-certifications';

// Certifications
export async function getCertifications(): Promise<SBACertification[]> {
  const res = await api.get(`${BASE}/certifications/`);
  return res.data;
}

export async function getCertification(id: string): Promise<SBACertification> {
  const res = await api.get(`${BASE}/certifications/${id}/`);
  return res.data;
}

export async function createCertification(
  data: Partial<SBACertification>
): Promise<SBACertification> {
  const res = await api.post(`${BASE}/certifications/`, data);
  return res.data;
}

export async function updateCertification(
  id: string,
  data: Partial<SBACertification>
): Promise<SBACertification> {
  const res = await api.patch(`${BASE}/certifications/${id}/`, data);
  return res.data;
}

export async function deleteCertification(id: string): Promise<void> {
  await api.delete(`${BASE}/certifications/${id}/`);
}

export async function initializeCertifications(): Promise<{
  initialized: string[];
  certifications: SBACertification[];
}> {
  const res = await api.post(`${BASE}/certifications/initialize/`);
  return res.data;
}

export async function updateCertSteps(
  id: string,
  steps: ApplicationStep[]
): Promise<SBACertification> {
  const res = await api.post(`${BASE}/certifications/${id}/update-steps/`, {
    application_steps: steps,
  });
  return res.data;
}

export async function getCertSummary(): Promise<CertSummary> {
  const res = await api.get(`${BASE}/certifications/summary/`);
  return res.data;
}

// NAICS Codes
export async function getNAICSCodes(): Promise<NAICSCode[]> {
  const res = await api.get(`${BASE}/naics-codes/`);
  return res.data;
}

export async function createNAICSCode(
  data: Partial<NAICSCode>
): Promise<NAICSCode> {
  const res = await api.post(`${BASE}/naics-codes/`, data);
  return res.data;
}

export async function updateNAICSCode(
  id: string,
  data: Partial<NAICSCode>
): Promise<NAICSCode> {
  const res = await api.patch(`${BASE}/naics-codes/${id}/`, data);
  return res.data;
}

export async function deleteNAICSCode(id: string): Promise<void> {
  await api.delete(`${BASE}/naics-codes/${id}/`);
}

export async function setNAICSPrimary(id: string): Promise<NAICSCode> {
  const res = await api.post(`${BASE}/naics-codes/${id}/set-primary/`);
  return res.data;
}
