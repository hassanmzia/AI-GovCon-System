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

// ── Pipeline Artifacts ──────────────────────────────────────────────────────

export interface DealArtifacts {
  opportunity_score: { total_score: number; recommendation: string } | null;
  technical_solution: { id: string; executive_summary: string; architecture_pattern: string; diagram_count: number } | null;
  pricing: { scenario_count: number; recommended: { name: string; total_price: string; margin_pct: number; probability_of_win: number } | null; cost_model: { total_cost: string; direct_labor: string } | null } | null;
  proposal: { id: string; title: string; status: string; section_count: number } | null;
  pricing_volume: { id: string; status: string; total_price: string } | null;
}

export async function getDealArtifacts(dealId: string): Promise<DealArtifacts> {
  const response = await api.get(`/deals/deals/${dealId}/artifacts/`);
  return response.data;
}

export async function rescoreDeal(dealId: string): Promise<void> {
  await api.post(`/deals/deals/${dealId}/rescore/`);
}

export async function runAllAgents(dealId: string): Promise<{ agents: string[] }> {
  const response = await api.post(`/deals/deals/${dealId}/run-agents/`);
  return response.data;
}

// ── Deal Activities & Agent Runs ────────────────────────────────────────────

export interface DealActivity {
  id: string;
  action: string;
  description: string;
  is_ai_action: boolean;
  metadata: Record<string, unknown>;
  actor_name?: string;
  created_at: string;
}

export interface AgentRun {
  id: string;
  agent_name: string;
  deal_id: string;
  action: string;
  status: "running" | "completed" | "failed" | "cancelled";
  started_at: string;
  completed_at: string | null;
  latency_ms: number | null;
  success: boolean | null;
  error_message: string;
}

export async function getDealActivities(
  dealId: string
): Promise<{ results: DealActivity[] }> {
  const response = await api.get("/deals/activities/", {
    params: { deal: dealId, limit: "50" },
  });
  return response.data;
}

export async function getDealAgentRuns(
  dealId: string
): Promise<{ results: AgentRun[] }> {
  const response = await api.get("/analytics/agent-runs/", {
    params: { deal_id: dealId, limit: "50" },
  });
  return response.data;
}
