export type ProposalStatus =
  | "draft"
  | "pink_team"
  | "red_team"
  | "gold_team"
  | "final"
  | "submitted";

export type SectionStatus =
  | "not_started"
  | "ai_drafted"
  | "in_review"
  | "revised"
  | "approved";

export type ReviewType = "pink" | "red" | "gold";

export type ReviewStatus = "scheduled" | "in_progress" | "completed";

export interface ProposalTemplate {
  id: string;
  name: string;
  description: string;
  volumes: Array<{
    volume_name: string;
    sections: Array<{
      name: string;
      description: string;
      page_limit: number | null;
    }>;
  }>;
  is_default: boolean;
}

export interface Proposal {
  id: string;
  deal: string;
  deal_name?: string;
  template: string | null;
  title: string;
  version: number;
  status: ProposalStatus;
  win_themes: string[];
  discriminators: string[];
  executive_summary: string;
  total_requirements: number;
  compliant_count: number;
  compliance_percentage: number;
  created_at: string;
  updated_at: string;
}

export interface ProposalSection {
  id: string;
  proposal: string;
  volume: string;
  section_number: string;
  title: string;
  order: number;
  ai_draft: string;
  human_content: string;
  final_content: string;
  status: SectionStatus;
  assigned_to: string | null;
  word_count: number;
  page_limit: number | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewCycle {
  id: string;
  proposal: string;
  review_type: ReviewType;
  status: ReviewStatus;
  scheduled_date: string | null;
  completed_date: string | null;
  overall_score: number | null;
  summary: string;
  reviewers: string[];
  created_at: string;
  updated_at: string;
}
