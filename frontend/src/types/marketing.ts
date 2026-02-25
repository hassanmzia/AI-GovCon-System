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
  goals: string[];
  metrics: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CompetitorProfile {
  id: string;
  name: string;
  core_competencies: string[];
  strengths: string[];
  weaknesses: string[];
  pricing_tendency: string;
  growth_trend: "up" | "flat" | "down" | string;
  known_contract_wins: string[];
  head_to_head_record: Record<string, unknown> | string;
  created_at: string;
  updated_at: string;
}

export interface MarketIntelligence {
  id: string;
  agency: string;
  mission: string;
  strategic_priorities: string[];
  budget_trends: string;
  technology_initiatives: string[];
  relationship_score: number;
  last_interaction: string | null;
  created_at: string;
  updated_at: string;
}
