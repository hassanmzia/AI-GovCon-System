import api from "@/lib/api";
import { Deal, DealStage } from "@/types/deal";
import { Opportunity } from "@/types/opportunity";
import { Proposal } from "@/types/proposal";

// ── Types ──────────────────────────────────────────────────────────────────

export interface PipelineStageCount {
  stage: DealStage;
  count: number;
}

export interface KpiMetrics {
  activeDeals: number;
  pipelineValue: number;
  openProposals: number;
  winRate: number | null;
  pendingApprovals: number;
  avgFitScore: number | null;
}

export interface PendingApproval {
  id: string;
  deal: string;
  deal_title: string;
  approval_type: string;
  status: "pending" | "approved" | "rejected";
  requested_by_detail: {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
  } | null;
  requested_from_detail: {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
  } | null;
  ai_recommendation: string;
  ai_confidence: number | null;
  decision_rationale: string;
  decided_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardData {
  deals: Deal[];
  approvals: PendingApproval[];
  opportunities: Opportunity[];
  proposals: Proposal[];
}

// ── Stage helpers ──────────────────────────────────────────────────────────

const ACTIVE_STAGES: DealStage[] = [
  "intake",
  "qualify",
  "bid_no_bid",
  "capture_plan",
  "proposal_dev",
  "red_team",
  "final_review",
  "submit",
  "post_submit",
  "award_pending",
  "contract_setup",
  "delivery",
];

const PIPELINE_STAGES: DealStage[] = [
  "intake",
  "qualify",
  "bid_no_bid",
  "capture_plan",
  "proposal_dev",
  "red_team",
  "final_review",
  "submit",
];

// ── Raw API fetchers ───────────────────────────────────────────────────────

export async function fetchAllDeals(): Promise<Deal[]> {
  const response = await api.get("/deals/deals/", {
    params: { ordering: "-created_at", page_size: 200 },
  });
  return response.data.results ?? response.data ?? [];
}

export async function fetchPendingApprovals(): Promise<PendingApproval[]> {
  const response = await api.get("/deals/approvals/", {
    params: { status: "pending", ordering: "-created_at", page_size: 100 },
  });
  return response.data.results ?? response.data ?? [];
}

export async function fetchRecentOpportunities(): Promise<Opportunity[]> {
  const response = await api.get("/opportunities/opportunities/", {
    params: { ordering: "-posted_date", page_size: 10 },
  });
  const data = response.data.results ?? response.data;
  return Array.isArray(data) ? data : [];
}

export async function fetchActiveProposals(): Promise<Proposal[]> {
  const response = await api.get("/proposals/proposals/", {
    params: { ordering: "-updated_at", page_size: 100 },
  });
  return response.data.results ?? response.data ?? [];
}

export async function decideApproval(
  approvalId: string,
  decision: "approved" | "rejected",
  rationale?: string
): Promise<PendingApproval> {
  const response = await api.post(`/deals/approvals/${approvalId}/decide/`, {
    status: decision,
    decision_rationale: rationale ?? "",
  });
  return response.data;
}

// ── Derived metrics ────────────────────────────────────────────────────────

export function computeKpis(
  deals: Deal[],
  approvals: PendingApproval[],
  proposals: Proposal[]
): KpiMetrics {
  const activeDeals = deals.filter((d) => ACTIVE_STAGES.includes(d.stage));
  const closedWon = deals.filter((d) => d.stage === "closed_won").length;
  const closedLost = deals.filter((d) => d.stage === "closed_lost").length;
  const closedTotal = closedWon + closedLost;

  const pipelineValue = activeDeals.reduce((sum, d) => {
    if (!d.estimated_value) return sum;
    const num = parseFloat(d.estimated_value);
    return isNaN(num) ? sum : sum + num;
  }, 0);

  const openProposals = proposals.filter((p) => p.status !== "submitted").length;

  const winRate = closedTotal > 0 ? (closedWon / closedTotal) * 100 : null;

  const scoresWithValues = activeDeals
    .map((d) => d.composite_score)
    .filter((s) => typeof s === "number" && s > 0);
  const avgFitScore =
    scoresWithValues.length > 0
      ? scoresWithValues.reduce((a, b) => a + b, 0) / scoresWithValues.length
      : null;

  return {
    activeDeals: activeDeals.length,
    pipelineValue,
    openProposals,
    winRate,
    pendingApprovals: approvals.length,
    avgFitScore,
  };
}

export function computePipelineDistribution(deals: Deal[]): PipelineStageCount[] {
  return PIPELINE_STAGES.map((stage) => ({
    stage,
    count: deals.filter((d) => d.stage === stage).length,
  }));
}

export function getRecentActivity(deals: Deal[], limit = 5): Deal[] {
  return [...deals]
    .sort(
      (a, b) =>
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )
    .slice(0, limit);
}

export function getUpcomingDeadlines(deals: Deal[], daysAhead = 30): Deal[] {
  const now = Date.now();
  const cutoff = now + daysAhead * 24 * 60 * 60 * 1000;
  return deals
    .filter((d) => {
      if (!d.due_date) return false;
      const due = new Date(d.due_date).getTime();
      return due >= now && due <= cutoff;
    })
    .sort(
      (a, b) =>
        new Date(a.due_date!).getTime() - new Date(b.due_date!).getTime()
    );
}
