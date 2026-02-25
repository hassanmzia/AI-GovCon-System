import api from "@/lib/api";

export interface ExecutiveSummary {
  active_deals: number;
  pipeline_value: number;
  proposals_in_progress: number;
  active_contracts: number;
  pending_approvals: number;
  upcoming_deadlines: number;
  win_rate: number | null;
  closed_won: number;
  closed_lost: number;
}

export interface PipelineFunnel {
  stages: Record<string, number>;
  conversion_rates: Record<string, number>;
  total_active: number;
}

export interface QuarterForecast {
  quarter: string;
  pipeline_value: number;
  weighted_value: number;
  deal_count: number;
}

export interface WinRateTrend {
  month: string;
  total: number;
  won: number;
  lost: number;
  win_rate: number;
  moving_avg: number | null;
}

export interface ExecutiveDashboardData {
  summary: ExecutiveSummary;
  pipeline_funnel: PipelineFunnel;
  revenue_forecast: QuarterForecast[];
  win_rate_trend: WinRateTrend[];
}

export interface PipelineLoad {
  active_deal_count: number;
  proposal_stage_count: number;
  total_pipeline_value: number;
  weighted_pipeline_value: number;
  stage_distribution: Record<string, number>;
}

export async function getExecutiveDashboard(): Promise<ExecutiveDashboardData> {
  const { data } = await api.get("/analytics/executive-dashboard/");
  return data;
}

export async function getPipelineLoad(): Promise<PipelineLoad> {
  const { data } = await api.get("/analytics/pipeline-load/");
  return data;
}
