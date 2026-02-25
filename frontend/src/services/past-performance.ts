import api from "@/lib/api";
import {
  PastPerformance,
  PastPerformanceMatch,
  CreatePastPerformancePayload,
} from "@/types/past-performance";

export async function getPastPerformanceRecords(params?: {
  search?: string;
  client_agency?: string;
  performance_rating?: string;
  domain?: string;
  is_active?: boolean;
  ordering?: string;
}): Promise<{ results: PastPerformance[]; count: number }> {
  const response = await api.get("/past-performance/records/", { params });
  return response.data;
}

export async function getPastPerformanceRecord(id: string): Promise<PastPerformance> {
  const response = await api.get(`/past-performance/records/${id}/`);
  return response.data;
}

export async function createPastPerformanceRecord(
  payload: CreatePastPerformancePayload
): Promise<PastPerformance> {
  const response = await api.post("/past-performance/records/", payload);
  return response.data;
}

export async function updatePastPerformanceRecord(
  id: string,
  payload: Partial<CreatePastPerformancePayload>
): Promise<PastPerformance> {
  const response = await api.patch(`/past-performance/records/${id}/`, payload);
  return response.data;
}

export async function deletePastPerformanceRecord(id: string): Promise<void> {
  await api.delete(`/past-performance/records/${id}/`);
}

export async function getMatchesForOpportunity(
  opportunityId: string
): Promise<PastPerformanceMatch[]> {
  const response = await api.get("/past-performance/matches/", {
    params: { opportunity: opportunityId, ordering: "-relevance_score" },
  });
  return response.data.results ?? response.data ?? [];
}

export async function triggerMatching(opportunityId: string): Promise<{ task_id: string }> {
  const response = await api.post("/past-performance/matches/trigger/", {
    opportunity_id: opportunityId,
  });
  return response.data;
}
