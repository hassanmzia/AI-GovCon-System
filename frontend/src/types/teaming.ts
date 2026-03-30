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
