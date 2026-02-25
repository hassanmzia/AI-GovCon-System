export type GoalCategory =
  | "revenue"
  | "market_entry"
  | "market_share"
  | "capability"
  | "relationship"
  | "portfolio"
  | "profitability";

export type GoalStatus = "on_track" | "at_risk" | "behind" | "achieved";

export type BidRecommendation = "bid" | "no_bid" | "conditional_bid";

export interface CompanyStrategy {
  id: string;
  version: number;
  effective_date: string;
  is_active: boolean;
  mission_statement: string;
  vision_3_year: string;
  target_revenue: string | null;
  target_win_rate: number;
  target_margin: number;
  target_agencies: string[];
  target_domains: string[];
  target_naics_codes: string[];
  growth_markets: string[];
  mature_markets: string[];
  exit_markets: string[];
  differentiators: string[];
  win_themes: string[];
  pricing_philosophy: string;
  teaming_strategy: string;
  max_concurrent_proposals: number;
  created_at: string;
}

export interface StrategicGoal {
  id: string;
  strategy: string;
  name: string;
  category: GoalCategory;
  metric: string;
  current_value: number;
  target_value: number;
  deadline: string;
  weight: number;
  status: GoalStatus;
  notes: string;
}

export interface PortfolioSnapshot {
  id: string;
  snapshot_date: string;
  active_deals: number;
  total_pipeline_value: string;
  weighted_pipeline: string;
  deals_by_agency: Record<string, number>;
  deals_by_domain: Record<string, number>;
  deals_by_stage: Record<string, number>;
  deals_by_size: Record<string, number>;
  capacity_utilization: number;
  concentration_risk: Record<string, unknown>;
  strategic_alignment_score: number;
  ai_recommendations: string[];
  strategy: string | null;
  created_at: string;
}

export interface StrategicScore {
  id: string;
  opportunity: string;
  strategic_score: number;
  technical_score: number;
  composite_score: number;
  recommendation: string;
  rationale: string;
  created_at: string;
}

export interface StrategyListResponse {
  results: CompanyStrategy[];
  count: number;
}

export interface StrategicGoalListResponse {
  results: StrategicGoal[];
  count: number;
}

export interface PortfolioSnapshotListResponse {
  results: PortfolioSnapshot[];
  count: number;
}

export interface StrategicScoreListResponse {
  results: StrategicScore[];
  count: number;
}
