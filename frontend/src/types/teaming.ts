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
  deal: string | { id: string; name: string; title?: string };
  deal_name?: string;
  partner_name: string;
  partner_uei?: string;
  partnership_type: PartnershipType;
  role: string;
  capabilities_contributed: string;
  agreement_status: AgreementStatus;
  agreement_date: string | null;
  work_share_percentage: number | null;
  notes: string;
  created_at: string;
  // Backend model fields (alternate naming)
  partner_company?: string;
  partner_contact_name?: string;
  partner_contact_email?: string;
  partner_contact_phone?: string;
  relationship_type?: string;
  status?: string;
  description?: string;
  responsibilities?: string[];
  revenue_share_percentage?: number | null;
  signed_agreement?: boolean;
  start_date?: string | null;
  end_date?: string | null;
}
