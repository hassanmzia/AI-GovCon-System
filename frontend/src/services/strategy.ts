import api from "@/lib/api";
import {
  CompanyStrategy,
  StrategicGoal,
  PortfolioSnapshot,
  StrategicScore,
  StrategyListResponse,
  StrategicGoalListResponse,
  PortfolioSnapshotListResponse,
  StrategicScoreListResponse,
} from "@/types/strategy";

export async function getStrategies(
  params?: Record<string, string>
): Promise<StrategyListResponse> {
  const response = await api.get("/strategy/strategies/", { params });
  return response.data;
}

export async function getStrategy(id: string): Promise<CompanyStrategy> {
  const response = await api.get(`/strategy/strategies/${id}/`);
  return response.data;
}

export async function createStrategy(
  data: Partial<CompanyStrategy>
): Promise<CompanyStrategy> {
  const response = await api.post("/strategy/strategies/", data);
  return response.data;
}

export async function updateStrategy(
  id: string,
  data: Partial<CompanyStrategy>
): Promise<CompanyStrategy> {
  const response = await api.patch(`/strategy/strategies/${id}/`, data);
  return response.data;
}

export async function getStrategicGoals(
  params?: Record<string, string>
): Promise<StrategicGoalListResponse> {
  const response = await api.get("/strategy/strategic-goals/", { params });
  return response.data;
}

export async function getPortfolioSnapshots(
  params?: Record<string, string>
): Promise<PortfolioSnapshotListResponse> {
  const response = await api.get("/strategy/portfolio-snapshots/", { params });
  return response.data;
}

export async function getStrategicScores(
  params?: Record<string, string>
): Promise<StrategicScoreListResponse> {
  const response = await api.get("/strategy/strategic-scores/", { params });
  return response.data;
}
