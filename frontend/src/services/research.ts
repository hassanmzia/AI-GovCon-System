import api from "@/lib/api";
import {
  ResearchProject,
  ResearchSource,
  CompetitorProfile,
  MarketIntelligence,
  ResearchProjectListResponse,
  CompetitorProfileListResponse,
  MarketIntelligenceListResponse,
  CreateResearchProjectPayload,
} from "@/types/research";

export async function getResearchProjects(
  params?: Record<string, string>
): Promise<ResearchProjectListResponse> {
  const response = await api.get("/research/projects/", { params });
  return response.data;
}

export async function getResearchProject(id: string): Promise<ResearchProject> {
  const response = await api.get(`/research/projects/${id}/`);
  return response.data;
}

export async function createResearchProject(
  data: CreateResearchProjectPayload
): Promise<ResearchProject> {
  const response = await api.post("/research/projects/", data);
  return response.data;
}

export async function getResearchSources(
  projectId: string
): Promise<{ results: ResearchSource[]; count: number }> {
  const response = await api.get("/research/sources/", {
    params: { project: projectId },
  });
  return response.data;
}

export async function getCompetitorProfiles(
  params?: Record<string, string>
): Promise<CompetitorProfileListResponse> {
  const response = await api.get("/research/competitors/", { params });
  return response.data;
}

export async function getMarketIntelligence(
  params?: Record<string, string>
): Promise<MarketIntelligenceListResponse> {
  const response = await api.get("/research/market-intelligence/", { params });
  return response.data;
}
