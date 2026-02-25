export type ResearchStatus = "pending" | "running" | "completed" | "failed";

export type ResearchType =
  | "market_analysis"
  | "competitive_intel"
  | "agency_analysis"
  | "technology_trends"
  | "incumbent_analysis"
  | "regulatory_landscape";

export type SourceType =
  | "web"
  | "government_db"
  | "news"
  | "academic"
  | "industry_report";

export type MarketIntelCategory =
  | "budget_trends"
  | "policy_changes"
  | "technology_shifts"
  | "procurement_patterns"
  | "workforce_trends";

export interface ResearchProject {
  id: string;
  deal: string;
  deal_title?: string;
  title: string;
  description: string;
  status: ResearchStatus;
  research_type: ResearchType;
  parameters: Record<string, unknown>;
  findings: Record<string, unknown>;
  executive_summary: string;
  sources: ResearchSourceSnippet[];
  ai_agent_trace_id: string | null;
  requested_by: string | null;
  requested_by_name?: string;
  created_at: string;
  completed_at?: string | null;
}

export interface ResearchSourceSnippet {
  url: string;
  title: string;
  relevance_score: number;
  snippet: string;
}

export interface ResearchSource {
  id: string;
  project: string;
  url: string;
  title: string;
  source_type: SourceType;
  content: string;
  relevance_score: number;
  extracted_data: Record<string, unknown>;
  fetched_at: string | null;
  created_at: string;
}

export interface CompetitorProfile {
  id: string;
  name: string;
  cage_code: string;
  duns_number: string;
  website: string;
  naics_codes: string[];
  contract_vehicles: string[];
  key_personnel: string[];
  revenue_range: string;
  employee_count: number | null;
  past_performance_summary: string;
  strengths: string[];
  weaknesses: string[];
  win_rate: number | null;
  is_active: boolean;
  created_at: string;
}

export interface MarketIntelligence {
  id: string;
  category: MarketIntelCategory;
  title: string;
  summary: string;
  detail: Record<string, unknown>;
  impact_assessment: string;
  affected_naics: string[];
  affected_agencies: string[];
  source_url: string;
  published_date: string | null;
  relevance_window_days: number;
  created_at: string;
}

export interface ResearchProjectListResponse {
  results: ResearchProject[];
  count: number;
}

export interface CompetitorProfileListResponse {
  results: CompetitorProfile[];
  count: number;
}

export interface MarketIntelligenceListResponse {
  results: MarketIntelligence[];
  count: number;
}

export interface CreateResearchProjectPayload {
  title: string;
  research_type: ResearchType;
  query?: string;
  deal: string;
  description?: string;
}
