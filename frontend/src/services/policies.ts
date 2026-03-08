import api from "@/lib/api";
import {
  BusinessPolicy,
  PolicyEvaluation,
  PolicyException,
} from "@/types/policy";

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function getPolicies(
  params?: Record<string, string>
): Promise<PaginatedResponse<BusinessPolicy>> {
  const { data } = await api.get("/policies/business-policies/", { params });
  return data;
}

export async function getPolicy(id: string): Promise<BusinessPolicy> {
  const { data } = await api.get(`/policies/business-policies/${id}/`);
  return data;
}

export async function createPolicy(
  payload: Partial<BusinessPolicy>
): Promise<BusinessPolicy> {
  const { data } = await api.post("/policies/business-policies/", payload);
  return data;
}

export async function updatePolicy(
  id: string,
  payload: Partial<BusinessPolicy>
): Promise<BusinessPolicy> {
  const { data } = await api.patch(`/policies/business-policies/${id}/`, payload);
  return data;
}

export async function evaluatePolicyForDeal(
  policyId: string,
  dealId: string
): Promise<PolicyEvaluation> {
  const { data } = await api.post(
    `/policies/business-policies/${policyId}/evaluate/`,
    { deal_id: dealId }
  );
  return data;
}

export async function evaluateAllPoliciesForDeal(
  dealId: string
): Promise<{
  deal_id: string;
  overall_outcome: string;
  policies_evaluated: number;
  evaluations: PolicyEvaluation[];
}> {
  const { data } = await api.post("/policies/evaluate-deal/", {
    deal_id: dealId,
  });
  return data;
}

export async function getEvaluations(
  params?: Record<string, string>
): Promise<PaginatedResponse<PolicyEvaluation>> {
  const { data } = await api.get("/policies/evaluations/", { params });
  return data;
}

export async function getExceptions(
  params?: Record<string, string>
): Promise<PaginatedResponse<PolicyException>> {
  const { data } = await api.get("/policies/exceptions/", { params });
  return data;
}

export async function approveException(id: string): Promise<PolicyException> {
  const { data } = await api.post(`/policies/exceptions/${id}/approve/`);
  return data;
}

export async function rejectException(id: string): Promise<PolicyException> {
  const { data } = await api.post(`/policies/exceptions/${id}/reject/`);
  return data;
}
