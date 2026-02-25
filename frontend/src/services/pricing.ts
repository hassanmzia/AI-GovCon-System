import api from "@/lib/api";
import {
  RateCard,
  PricingScenario,
  LOEEstimate,
  CostModel,
  PricingApproval,
} from "@/types/pricing";

export async function getRateCards(
  params?: Record<string, string>
): Promise<{ results: RateCard[]; count: number }> {
  const response = await api.get("/pricing/rate-cards/", { params });
  return response.data;
}

export async function getRateCard(id: string): Promise<RateCard> {
  const response = await api.get(`/pricing/rate-cards/${id}/`);
  return response.data;
}

export async function getScenarios(
  params?: Record<string, string>
): Promise<{ results: PricingScenario[]; count: number }> {
  const response = await api.get("/pricing/scenarios/", { params });
  return response.data;
}

export async function getScenario(id: string): Promise<PricingScenario> {
  const response = await api.get(`/pricing/scenarios/${id}/`);
  return response.data;
}

export async function createScenario(
  data: Partial<PricingScenario>
): Promise<PricingScenario> {
  const response = await api.post("/pricing/scenarios/", data);
  return response.data;
}

export async function getLOEEstimates(
  params?: Record<string, string>
): Promise<{ results: LOEEstimate[]; count: number }> {
  const response = await api.get("/pricing/loe-estimates/", { params });
  return response.data;
}

export async function getCostModels(
  params?: Record<string, string>
): Promise<{ results: CostModel[]; count: number }> {
  const response = await api.get("/pricing/cost-models/", { params });
  return response.data;
}

export async function getPricingApprovals(
  params?: Record<string, string>
): Promise<{ results: PricingApproval[]; count: number }> {
  const response = await api.get("/pricing/approvals/", { params });
  return response.data;
}
