export type DocumentType =
  | "rfp"
  | "rfi"
  | "rfq"
  | "sources_sought"
  | "amendment"
  | "qa_response"
  | "attachment"
  | "other";

export type ExtractionStatus = "pending" | "processing" | "completed" | "failed";

export type RequirementType = "mandatory" | "desirable" | "informational";

export type ResponseStatus =
  | "not_started"
  | "in_progress"
  | "drafted"
  | "reviewed"
  | "final";

export type ComplianceStatus =
  | "compliant"
  | "partial"
  | "non_compliant"
  | "not_assessed";

export interface RFPDocument {
  id: string;
  deal: string;
  deal_name?: string;
  title: string;
  document_type: DocumentType;
  file_url?: string;
  file_name: string;
  file_size: number;
  file_type: string;
  extraction_status: ExtractionStatus;
  page_count: number | null;
  version: number;
  amendment_number?: number | null;
  status?: string;
  parsing_status?: ExtractionStatus;
  uploaded_at?: string;
  created_at: string;
  updated_at: string;
}

export interface RFPRequirement {
  id: string;
  rfp_document: string;
  requirement_id: string;
  requirement_text: string;
  section_reference: string;
  requirement_type: RequirementType;
  category: string;
  evaluation_weight: number | null;
}

export interface ComplianceMatrixItem {
  id: string;
  rfp_document: string;
  requirement: string;
  requirement_id?: string;
  requirement_text?: string;
  requirement_type?: RequirementType;
  proposal_section: string;
  proposal_page: string;
  response_owner: string | null;
  response_owner_name?: string;
  response_status: ResponseStatus;
  ai_draft_response: string;
  human_final_response: string;
  compliance_status: ComplianceStatus;
  compliance_notes: string;
  evidence_references: string[];
}

export interface Amendment {
  id: string;
  rfp_document: string;
  amendment_number: number;
  title: string;
  summary: string;
  is_material: boolean;
  requires_compliance_update: boolean;
  detected_at: string;
  reviewed: boolean;
}
