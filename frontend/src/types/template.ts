export type TemplateCategory =
  | "proposal"
  | "capability_statement"
  | "past_performance"
  | "email"
  | "contract"
  | "checklist"
  | "pitch_deck"
  | "guide"
  | "other";

export type TemplateFormat = "docx" | "pdf" | "pptx" | "xlsx" | "txt";

export interface TemplateVariable {
  name: string;
  label: string;
  default: string;
}

export interface DocumentTemplate {
  id: string;
  name: string;
  description: string;
  category: TemplateCategory;
  file_format: TemplateFormat;
  file?: string;
  file_url: string | null;
  file_size: number;
  variables: TemplateVariable[];
  version: string;
  source: string;
  tags: string[];
  is_active: boolean;
  is_default: boolean;
  usage_count: number;
  uploaded_by: string | null;
  uploaded_by_name: string;
  created_at: string;
  updated_at: string;
}

export const CATEGORY_LABELS: Record<TemplateCategory, string> = {
  proposal: "Proposal Template",
  capability_statement: "Capability Statement",
  past_performance: "Past Performance",
  email: "Email Template",
  contract: "Contract Template",
  checklist: "Checklist",
  pitch_deck: "Pitch Deck",
  guide: "Guide / Reference",
  other: "Other",
};

export const FORMAT_LABELS: Record<TemplateFormat, string> = {
  docx: "Word (.docx)",
  pdf: "PDF (.pdf)",
  pptx: "PowerPoint (.pptx)",
  xlsx: "Excel (.xlsx)",
  txt: "Plain Text",
};
