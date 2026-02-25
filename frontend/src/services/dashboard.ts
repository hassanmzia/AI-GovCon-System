import {
  fetchAllDeals,
  fetchPendingApprovals,
  fetchRecentOpportunities,
  fetchActiveProposals,
  computeKpis,
  computePipelineDistribution,
  getRecentActivity,
  getUpcomingDeadlines,
  KpiMetrics,
  PipelineStageCount,
  PendingApproval,
} from "@/services/analytics";
import { Deal } from "@/types/deal";
import { Opportunity } from "@/types/opportunity";
import { Proposal } from "@/types/proposal";

// ── Aggregated dashboard snapshot ─────────────────────────────────────────

export interface DashboardSnapshot {
  kpis: KpiMetrics;
  pipelineDistribution: PipelineStageCount[];
  recentActivity: Deal[];
  upcomingDeadlines: Deal[];
  pendingApprovals: PendingApproval[];
  recentOpportunities: Opportunity[];
  proposals: Proposal[];
  fetchedAt: Date;
}

// Fallback static data used when specific API calls fail
const FALLBACK_KPIS: KpiMetrics = {
  activeDeals: 0,
  pipelineValue: 0,
  openProposals: 0,
  winRate: null,
  pendingApprovals: 0,
  avgFitScore: null,
};

// ── Main aggregation function ──────────────────────────────────────────────

/**
 * Fetches all dashboard data concurrently.
 * Each section degrades gracefully: if one API call fails the rest
 * of the dashboard still renders with the successfully fetched data.
 */
export async function fetchDashboardSnapshot(): Promise<DashboardSnapshot> {
  const [dealsResult, approvalsResult, oppsResult, proposalsResult] =
    await Promise.allSettled([
      fetchAllDeals(),
      fetchPendingApprovals(),
      fetchRecentOpportunities(),
      fetchActiveProposals(),
    ]);

  const deals: Deal[] =
    dealsResult.status === "fulfilled" ? dealsResult.value : [];
  const approvals: PendingApproval[] =
    approvalsResult.status === "fulfilled" ? approvalsResult.value : [];
  const opportunities: Opportunity[] =
    oppsResult.status === "fulfilled" ? oppsResult.value : [];
  const proposals: Proposal[] =
    proposalsResult.status === "fulfilled" ? proposalsResult.value : [];

  // Log any failures for debugging (non-blocking)
  if (dealsResult.status === "rejected") {
    console.warn("[dashboard] deals fetch failed:", dealsResult.reason);
  }
  if (approvalsResult.status === "rejected") {
    console.warn("[dashboard] approvals fetch failed:", approvalsResult.reason);
  }
  if (oppsResult.status === "rejected") {
    console.warn("[dashboard] opportunities fetch failed:", oppsResult.reason);
  }
  if (proposalsResult.status === "rejected") {
    console.warn("[dashboard] proposals fetch failed:", proposalsResult.reason);
  }

  const kpis =
    deals.length > 0 || proposals.length > 0
      ? computeKpis(deals, approvals, proposals)
      : FALLBACK_KPIS;

  // Merge approval count from the approvals endpoint (most accurate)
  kpis.pendingApprovals = approvals.length;

  return {
    kpis,
    pipelineDistribution: computePipelineDistribution(deals),
    recentActivity: getRecentActivity(deals, 5),
    upcomingDeadlines: getUpcomingDeadlines(deals, 30),
    pendingApprovals: approvals,
    recentOpportunities: opportunities.slice(0, 3),
    proposals,
    fetchedAt: new Date(),
  };
}
