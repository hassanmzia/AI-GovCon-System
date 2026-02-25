export interface FARClause {
  id: string;
  clause_number: string;
  title: string;
  clause_type: string;
  source: string;
  text: string;
  is_mandatory: boolean;
  applicability: string;
  notes: string;
  category?: string;
  full_text?: string;
  plain_language_summary?: string;
  related_dfars?: string[];
  compliance_checklist?: string[];
  applicability_threshold?: number | null;
  last_updated?: string | null;
}

export interface RegulatoryRequirement {
  id: string;
  name: string;
  regulation_type: string;
  description: string;
  applies_to: string;
  compliance_deadline: string | null;
  status: string;
  regulation_source?: string;
  reference_number?: string;
  title?: string;
  effective_date?: string | null;
  expiration_date?: string | null;
}

export interface ComplianceAssessment {
  id: string;
  deal: string | { id: string; name: string; title?: string };
  deal_name?: string;
  assessment_date: string;
  overall_status: string;
  risk_level: "low" | "medium" | "high" | "critical";
  findings_count: number;
  recommendations: string[] | string;
  assessor: string | { id: string; name: string } | null;
  status?: string;
  far_compliance_score?: number;
  dfars_compliance_score?: number;
  overall_risk_level?: string;
  findings?: unknown[];
  created_at?: string;
}

export interface LegalRisk {
  id: string;
  deal: string | { id: string; name: string; title?: string };
  deal_name?: string;
  risk_type: string;
  description: string;
  severity: "low" | "medium" | "high" | "critical";
  probability: string;
  mitigation_strategy: string;
  status: "identified" | "mitigating" | "accepted" | "resolved" | "mitigated";
  identified_date?: string;
  title?: string;
  created_at?: string;
  resolved_at?: string | null;
}

export interface ContractReviewNote {
  id: string;
  contract: string | { id: string; name: string };
  deal?: string | { id: string; name: string };
  note_type: "concern" | "suggestion" | "approval" | "question";
  section_reference: string;
  concern: string;
  recommendation: string;
  severity: "low" | "medium" | "high";
  resolved: boolean;
  section?: string;
  note_text?: string;
  priority?: string;
  status?: string;
  response?: string;
  created_at?: string;
}
