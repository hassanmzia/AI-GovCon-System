import api from "@/lib/api";
import {
  MarketingCampaign,
  CompetitorProfile,
  MarketIntelligence,
} from "@/types/marketing";

export async function getCampaigns(
  params?: Record<string, string>
): Promise<{ results: MarketingCampaign[]; count: number }> {
  const response = await api.get("/marketing/campaigns/", { params });
  return response.data;
}

export async function getCampaign(id: string): Promise<MarketingCampaign> {
  const response = await api.get(`/marketing/campaigns/${id}/`);
  return response.data;
}

export async function createCampaign(
  data: Partial<MarketingCampaign>
): Promise<MarketingCampaign> {
  const response = await api.post("/marketing/campaigns/", data);
  return response.data;
}

export async function updateCampaign(
  id: string,
  data: Partial<MarketingCampaign>
): Promise<MarketingCampaign> {
  const response = await api.patch(`/marketing/campaigns/${id}/`, data);
  return response.data;
}

export async function getCompetitorProfiles(
  params?: Record<string, string>
): Promise<{ results: CompetitorProfile[]; count: number }> {
  const response = await api.get("/research/competitors/", { params });
  return response.data;
}

export async function getMarketIntelligence(
  params?: Record<string, string>
): Promise<{ results: MarketIntelligence[]; count: number }> {
  const response = await api.get("/research/market-intelligence/", { params });
  return response.data;
}
