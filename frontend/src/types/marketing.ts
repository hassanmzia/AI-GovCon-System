export interface MarketingCampaign {
  id: string;
  name: string;
  description: string;
  channel: string;
  status: "planning" | "active" | "paused" | "completed" | "cancelled";
  target_audience: string;
  start_date: string | null;
  end_date: string | null;
  budget: string | null;
  owner: string | null;
  owner_username?: string;
  goals: string[];
  metrics: Record<string, unknown>;
  related_deals?: string[];
  created_at: string;
  updated_at: string;
}

export interface CompetitorProfile {
  id: string;
  name: string;
  cage_code: string;
  duns_number: string;
  website: string;
  naics_codes: string[];
  contract_vehicles: string[];
  key_personnel: Record<string, unknown>[];
  revenue_range: string;
  employee_count: number | null;
  past_performance_summary: string;
  strengths: string[];
  weaknesses: string[];
  win_rate: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MarketIntelligence {
  id: string;
  category: string;
  category_display: string;
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
  updated_at: string;
}
