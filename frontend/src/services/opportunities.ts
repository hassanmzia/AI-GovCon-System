import api from "@/lib/api";
import { Opportunity } from "@/types/opportunity";

export async function getOpportunities(
  params?: Record<string, string>
): Promise<{ results: Opportunity[]; count: number }> {
  const response = await api.get("/opportunities/", { params });
  return response.data;
}

export async function getOpportunity(id: string): Promise<Opportunity> {
  const response = await api.get(`/opportunities/${id}/`);
  return response.data;
}

export async function triggerScan(): Promise<{ message: string }> {
  const response = await api.post("/opportunities/trigger_scan/");
  return response.data;
}

export async function getDigests(): Promise<unknown> {
  const response = await api.get("/opportunities/digests/");
  return response.data;
}
