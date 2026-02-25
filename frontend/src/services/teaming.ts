import api from "@/lib/api";
import { TeamingPartnership } from "@/types/teaming";

export async function getPartnerships(
  params?: Record<string, string>
): Promise<{ results: TeamingPartnership[]; count: number }> {
  const response = await api.get("/teaming/partnerships/", { params });
  return response.data;
}

export async function getPartnership(id: string): Promise<TeamingPartnership> {
  const response = await api.get(`/teaming/partnerships/${id}/`);
  return response.data;
}

export async function createPartnership(
  data: Partial<TeamingPartnership>
): Promise<TeamingPartnership> {
  const response = await api.post("/teaming/partnerships/", data);
  return response.data;
}

export async function updatePartnership(
  id: string,
  data: Partial<TeamingPartnership>
): Promise<TeamingPartnership> {
  const response = await api.patch(`/teaming/partnerships/${id}/`, data);
  return response.data;
}

export async function deletePartnership(id: string): Promise<void> {
  await api.delete(`/teaming/partnerships/${id}/`);
}
