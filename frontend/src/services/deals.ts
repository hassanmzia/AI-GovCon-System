import api from "@/lib/api";
import {
  Deal,
  DealListResponse,
  DealStageHistory,
  DealTask,
  DealApproval,
  DealPipelineSummary,
  CreateDealPayload,
  TransitionStagePayload,
  ApprovalDecisionPayload,
} from "@/types/deal";

export async function getDeals(
  params?: Record<string, string>
): Promise<DealListResponse> {
  const response = await api.get("/deals/deals/", { params });
  return response.data;
}

export async function getDeal(id: string): Promise<Deal> {
  const response = await api.get(`/deals/deals/${id}/`);
  return response.data;
}

export async function createDeal(payload: CreateDealPayload): Promise<Deal> {
  const response = await api.post("/deals/deals/", payload);
  return response.data;
}

export async function updateDeal(
  id: string,
  payload: Partial<CreateDealPayload>
): Promise<Deal> {
  const response = await api.patch(`/deals/deals/${id}/`, payload);
  return response.data;
}

export async function transitionDealStage(
  id: string,
  payload: TransitionStagePayload
): Promise<Deal> {
  const response = await api.post(`/deals/deals/${id}/transition/`, payload);
  return response.data;
}

export async function getDealStageHistory(
  id: string
): Promise<DealStageHistory[]> {
  const response = await api.get(`/deals/deals/${id}/stage-history/`);
  return response.data;
}

export async function getDealPipelineSummary(
  id: string
): Promise<DealPipelineSummary> {
  const response = await api.get(`/deals/deals/${id}/pipeline-summary/`);
  return response.data;
}

export async function requestApproval(id: string): Promise<DealApproval> {
  const response = await api.post(`/deals/deals/${id}/request-approval/`);
  return response.data;
}

export async function getTasks(
  params?: Record<string, string>
): Promise<{ results: DealTask[]; count: number }> {
  const response = await api.get("/deals/tasks/", { params });
  return response.data;
}

export async function completeTask(
  taskId: string
): Promise<DealTask> {
  const response = await api.post(`/deals/tasks/${taskId}/complete/`);
  return response.data;
}

export async function getApprovals(
  params?: Record<string, string>
): Promise<{ results: DealApproval[]; count: number }> {
  const response = await api.get("/deals/approvals/", { params });
  return response.data;
}

export async function decideApproval(
  approvalId: string,
  payload: ApprovalDecisionPayload
): Promise<DealApproval> {
  const response = await api.post(
    `/deals/approvals/${approvalId}/decide/`,
    payload
  );
  return response.data;
}
