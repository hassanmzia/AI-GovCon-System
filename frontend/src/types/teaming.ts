export type PartnershipType =
  | "prime"
  | "subcontractor"
  | "joint_venture"
  | "mentor_protege"
  | "teaming_agreement"
  | "prime_contractor"
  | "mentor"
  | "protege"
  | "strategic_partner";

export type AgreementStatus =
  | "identifying"
  | "evaluating"
  | "negotiating"
  | "signed"
  | "active"
  | "inactive"
  | "prospect"
  | "completed"
  | "terminated";

export interface TeamingPartnership {
  id: string;
  deal: string;
  deal_name?: string;
  partner_company: string;
  partner_contact_name?: string;
  partner_contact_email?: string;
  partner_contact_phone?: string;
  relationship_type: string;
  status: AgreementStatus;
  description?: string;
  responsibilities?: string[];
  revenue_share_percentage?: number | null;
  percentage_of_work?: number | null;
  signed_agreement?: boolean;
  agreement_date?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  terms_and_conditions?: string;
  partner_naics_codes?: string[];
  partner_certifications?: string[];
  partner_clearance_level?: string;
  partner_past_performance?: Array<{ project?: string; agency?: string; relevance?: string }>;
  partner_key_personnel?: Array<{ name?: string; role?: string; qualifications?: string }>;
  disclosure_sections?: string[];
  exclusivity?: boolean;
  ip_ownership?: string;
  dispute_resolution?: string;
  owner?: string | null;
  owner_username?: string;
  created_at: string;
  updated_at?: string;
  // Compatibility aliases used by helpers
  partner_name?: string;
  partner_uei?: string;
  partnership_type?: PartnershipType;
  agreement_status?: AgreementStatus;
  work_share_percentage?: number | null;
  role?: string;
  capabilities_contributed?: string;
  notes?: string;
}

export interface TeamingPartner {
  id: string;
  name: string;
  uei: string;
  cage_code?: string;
  duns_number?: string;
  naics_codes: string[];
  capabilities: string[];
  contract_vehicles: string[];
  labor_categories?: string[];
  sb_certifications: string[];
  is_small_business: boolean;
  clearance_level: string;
  performance_history: string;
  reliability_score: number;
  has_cpars_issues?: boolean;
  risk_level: string;
  past_revenue: number;
  employee_count: number;
  primary_agencies: string[];
  headquarters: string;
  website?: string;
  primary_contact_name?: string;
  primary_contact_email?: string;
  primary_contact_phone?: string;
  is_active: boolean;
  notes?: string;
  tags: string[];
  is_channel_partner: boolean;
  referral_fee_pct?: number | null;
  co_sell_opportunities: number;
  co_sell_wins: number;
  mentor_protege_role?: string;
  mentor_protege_program?: string;
  mentor_protege_start?: string | null;
  mentor_protege_end?: string | null;
  partnerships_count?: number;
  created_at: string;
  updated_at?: string;
}

export interface TeamingAgreement {
  id: string;
  partnership: string;
  partnership_name?: string;
  deal_name?: string;
  agreement_type: "nda" | "loi" | "teaming" | "subcontract" | "jv_agreement";
  status: "draft" | "sent" | "under_review" | "signed" | "active" | "expired" | "terminated";
  title?: string;
  document?: string;
  document_text?: string;
  sent_date?: string | null;
  signed_date?: string | null;
  effective_date?: string | null;
  expiry_date?: string | null;
  exclusivity: boolean;
  work_scope?: string;
  work_share_pct?: number | null;
  ip_ownership?: string;
  our_signatory?: string;
  partner_signatory?: string;
  outcome?: string;
  created_by?: string;
  created_at: string;
  updated_at?: string;
}

export const CLEARANCE_LABELS: Record<string, string> = {
  none: "None",
  public_trust: "Public Trust",
  secret: "Secret",
  top_secret: "Top Secret",
  ts_sci: "TS/SCI",
};

export const RISK_COLORS: Record<string, string> = {
  low: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
};

export const AGREEMENT_TYPE_LABELS: Record<string, string> = {
  nda: "NDA",
  loi: "Letter of Intent",
  teaming: "Teaming Agreement",
  subcontract: "Subcontract",
  jv_agreement: "JV Agreement",
};
