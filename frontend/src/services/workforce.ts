import api from "@/lib/api";
import { Employee, Assignment, HiringRequisition, DemandForecast } from "@/types/workforce";

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function getEmployees(
  params?: Record<string, string>
): Promise<PaginatedResponse<Employee>> {
  const { data } = await api.get("/workforce/employees/", { params });
  return data;
}

export async function getEmployee(id: string): Promise<Employee> {
  const { data } = await api.get(`/workforce/employees/${id}/`);
  return data;
}

export async function createEmployee(
  payload: Partial<Employee>
): Promise<Employee> {
  const { data } = await api.post("/workforce/employees/", payload);
  return data;
}

export async function getAssignments(
  params?: Record<string, string>
): Promise<PaginatedResponse<Assignment>> {
  const { data } = await api.get("/workforce/assignments/", { params });
  return data;
}

export async function getHiringRequisitions(
  params?: Record<string, string>
): Promise<PaginatedResponse<HiringRequisition>> {
  const { data } = await api.get("/workforce/hiring-requisitions/", { params });
  return data;
}

export async function createHiringRequisition(
  payload: Partial<HiringRequisition>
): Promise<HiringRequisition> {
  const { data } = await api.post("/workforce/hiring-requisitions/", payload);
  return data;
}

export async function getDemandForecast(): Promise<DemandForecast> {
  const { data } = await api.get("/workforce/analytics/demand-forecast/");
  return data;
}
