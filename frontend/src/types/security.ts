export type ImplementationStatus =
  | "implemented"
  | "partially_implemented"
  | "not_implemented"
  | "not_applicable"
  | "planned"
  | "partial";

export type ReportType =
  | "gap_analysis"
  | "ssp_draft"
  | "assessment_report"
  | "cmmc_readiness"
  | "readiness_assessment"
  | "poam"
  | "ssp_section"
  | "authorization_package";

export interface SecurityFramework {
  id: string;
  name: string;
  version: string;
  description: string;
  framework_type: string;
  controls_count: number;
  control_families?: string[];
  is_active?: boolean;
  created_at?: string;
}

export interface SecurityControl {
  id: string;
  framework: string | { id: string; name: string; version: string };
  framework_name?: string;
  control_id: string;
  title: string;
  description: string;
  control_family: string;
  implementation_status: ImplementationStatus;
  priority: string;
  family?: string;
  baseline_impact?: string;
  implementation_guidance?: string;
}

export interface SecurityControlMapping {
  id: string;
  deal: string | { id: string; name: string; title?: string };
  deal_name?: string;
  control: string | { id: string; control_id: string; title: string; framework?: string | { id: string; name: string; version: string } };
  control_id?: string;
  control_title?: string;
  framework_name?: string;
  mapping_status: ImplementationStatus;
  implementation_notes: string;
  evidence: string;
  gap_description: string;
  implementation_status?: ImplementationStatus;
  created_at?: string;
}

export interface SecurityComplianceReport {
  id: string;
  deal: string | { id: string; name: string; title?: string };
  deal_name?: string;
  report_type: ReportType;
  framework: string | { id: string; name: string; version: string };
  framework_name?: string;
  overall_score: number;
  compliant_controls: number;
  total_controls: number;
  gaps_identified: number;
  created_at: string;
  // Backend model fields
  status?: string;
  overall_compliance_pct?: number;
  controls_implemented?: number;
  controls_partial?: number;
  controls_planned?: number;
  controls_na?: number;
  gaps?: unknown[];
  findings?: unknown[];
}

export interface ComplianceRequirement {
  id: string;
  deal: string | { id: string; name: string; title?: string };
  deal_name?: string;
  requirement_text: string;
  framework_reference: string;
  status: string;
  priority: string;
  assigned_to: string | null;
  category?: string;
  current_status?: string;
  source_document?: string;
  gap_description?: string;
  notes?: string;
  created_at?: string;
}
