"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  fetchAllDeals,
  fetchPendingApprovals,
  fetchActiveProposals,
  fetchRecentOpportunities,
  computeKpis,
  computePipelineDistribution,
  getUpcomingDeadlines,
  decideApproval,
  PendingApproval,
  KpiMetrics,
  PipelineStageCount,
} from "@/services/analytics";
import { Deal } from "@/types/deal";
import { Proposal } from "@/types/proposal";
import { Opportunity } from "@/types/opportunity";
import {
  TrendingUp,
  DollarSign,
  FileEdit,
  CheckCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
  Calendar,
  BarChart3,
  Target,
  Clock,
} from "lucide-react";

// ── Stage display helpers ──────────────────────────────────────────────────

const STAGE_LABELS: Record<string, string> = {
  intake: "Intake",
  qualify: "Qualify",
  bid_no_bid: "Bid/No-Bid",
  capture_plan: "Capture Plan",
  proposal_dev: "Proposal Dev",
  red_team: "Red Team",
  final_review: "Final Review",
  submit: "Submitted",
};

const STAGE_COLORS: Record<string, string> = {
  intake: "bg-slate-400",
  qualify: "bg-blue-400",
  bid_no_bid: "bg-yellow-400",
  capture_plan: "bg-orange-400",
  proposal_dev: "bg-purple-400",
  red_team: "bg-red-400",
  final_review: "bg-indigo-400",
  submit: "bg-green-400",
};

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// ── Sub-components ─────────────────────────────────────────────────────────

function KpiCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="mt-1 text-3xl font-bold text-foreground">{value}</p>
            {subtitle && (
              <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
            )}
          </div>
          <div className={`rounded-full p-2 ${color}`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function PipelineBar({ distribution }: { distribution: PipelineStageCount[] }) {
  const total = distribution.reduce((s, d) => s + d.count, 0) || 1;
  return (
    <div className="space-y-3">
      {distribution.map((d) => (
        <div key={d.stage} className="flex items-center gap-3">
          <span className="w-28 shrink-0 text-xs text-muted-foreground text-right">
            {STAGE_LABELS[d.stage] ?? d.stage}
          </span>
          <div className="flex-1 overflow-hidden rounded-full bg-secondary h-3">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${
                STAGE_COLORS[d.stage] ?? "bg-primary"
              }`}
              style={{ width: `${(d.count / total) * 100}%` }}
            />
          </div>
          <span className="w-6 shrink-0 text-xs font-medium text-foreground text-right">
            {d.count}
          </span>
        </div>
      ))}
    </div>
  );
}

function WinRateGauge({ winRate }: { winRate: number | null }) {
  if (winRate === null) {
    return (
      <div className="flex flex-col items-center justify-center py-8">
        <p className="text-4xl font-bold text-muted-foreground">--</p>
        <p className="mt-2 text-sm text-muted-foreground">No closed deals yet</p>
      </div>
    );
  }
  const color =
    winRate >= 60
      ? "text-green-600"
      : winRate >= 40
      ? "text-yellow-600"
      : "text-red-600";
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <p className={`text-5xl font-bold ${color}`}>{winRate.toFixed(0)}%</p>
      <p className="mt-2 text-sm text-muted-foreground">Win Rate</p>
      <p className="text-xs text-muted-foreground mt-1">
        {winRate >= 60 ? "Excellent" : winRate >= 40 ? "Good" : "Needs improvement"}
      </p>
    </div>
  );
}

function ApprovalRow({
  approval,
  onDecide,
}: {
  approval: PendingApproval;
  onDecide: (id: string, decision: "approved" | "rejected") => void;
}) {
  const [deciding, setDeciding] = useState(false);

  const handleDecide = async (decision: "approved" | "rejected") => {
    setDeciding(true);
    await onDecide(approval.id, decision);
    setDeciding(false);
  };

  return (
    <div className="flex items-center justify-between gap-4 py-3 border-b last:border-b-0">
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">
          {approval.deal_title}
        </p>
        <p className="text-xs text-muted-foreground">
          {approval.approval_type.replace(/_/g, " ")} ·{" "}
          {formatDate(approval.created_at)}
        </p>
        {approval.ai_recommendation && (
          <p className="text-xs text-primary mt-0.5">
            AI: {approval.ai_recommendation}
            {approval.ai_confidence != null &&
              ` (${(approval.ai_confidence * 100).toFixed(0)}%)`}
          </p>
        )}
      </div>
      <div className="flex gap-2 shrink-0">
        <Button
          size="sm"
          variant="outline"
          className="text-red-600 border-red-200 hover:bg-red-50"
          onClick={() => handleDecide("rejected")}
          disabled={deciding}
        >
          {deciding ? <Loader2 className="h-3 w-3 animate-spin" /> : "Reject"}
        </Button>
        <Button
          size="sm"
          onClick={() => handleDecide("approved")}
          disabled={deciding}
        >
          {deciding ? <Loader2 className="h-3 w-3 animate-spin" /> : "Approve"}
        </Button>
      </div>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [d, a, p, o] = await Promise.all([
        fetchAllDeals(),
        fetchPendingApprovals(),
        fetchActiveProposals(),
        fetchRecentOpportunities(),
      ]);
      setDeals(d);
      setApprovals(a);
      setProposals(p);
      setOpportunities(o);
    } catch {
      setError("Failed to load analytics data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const kpis: KpiMetrics = computeKpis(deals, approvals, proposals);
  const pipeline = computePipelineDistribution(deals);
  const deadlines = getUpcomingDeadlines(deals, 30);

  const closedWon = deals.filter((d) => d.stage === "closed_won").length;
  const closedLost = deals.filter((d) => d.stage === "closed_lost").length;

  const handleDecide = async (id: string, decision: "approved" | "rejected") => {
    try {
      await decideApproval(id, decision);
      setApprovals((prev) => prev.filter((a) => a.id !== id));
    } catch {
      // Silently fail — approval list stays intact for retry
    }
  };

  // Proposal breakdown
  const proposalByStatus: Record<string, number> = {};
  for (const p of proposals) {
    proposalByStatus[p.status] = (proposalByStatus[p.status] ?? 0) + 1;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">Loading analytics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-red-600">{error}</p>
        <Button variant="outline" onClick={load}>
          <RefreshCw className="mr-2 h-4 w-4" /> Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Analytics</h1>
          <p className="text-muted-foreground">
            Pipeline health, win rates, and approval queue
          </p>
        </div>
        <Button variant="outline" onClick={load}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Active Deals"
          value={String(kpis.activeDeals)}
          subtitle={`${closedWon} won · ${closedLost} lost`}
          icon={TrendingUp}
          color="bg-blue-500"
        />
        <KpiCard
          title="Pipeline Value"
          value={formatCurrency(kpis.pipelineValue)}
          subtitle="Active stages only"
          icon={DollarSign}
          color="bg-green-500"
        />
        <KpiCard
          title="Open Proposals"
          value={String(kpis.openProposals)}
          subtitle="Not yet submitted"
          icon={FileEdit}
          color="bg-purple-500"
        />
        <KpiCard
          title="Pending Approvals"
          value={String(kpis.pendingApprovals)}
          subtitle={kpis.pendingApprovals > 0 ? "Action required" : "All clear"}
          icon={CheckCircle}
          color={kpis.pendingApprovals > 0 ? "bg-orange-500" : "bg-slate-400"}
        />
      </div>

      {/* Second row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Pipeline distribution */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-4 w-4" />
              Pipeline Distribution
            </CardTitle>
            <span className="text-xs text-muted-foreground">
              {kpis.activeDeals} active deals
            </span>
          </CardHeader>
          <CardContent>
            {pipeline.every((d) => d.count === 0) ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                No deals in pipeline yet
              </p>
            ) : (
              <PipelineBar distribution={pipeline} />
            )}
          </CardContent>
        </Card>

        {/* Win rate */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Target className="h-4 w-4" />
              Win Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <WinRateGauge winRate={kpis.winRate} />
            <div className="mt-4 grid grid-cols-2 gap-2 text-center text-sm">
              <div className="rounded-md bg-green-50 py-2">
                <p className="font-bold text-green-700">{closedWon}</p>
                <p className="text-xs text-green-600">Won</p>
              </div>
              <div className="rounded-md bg-red-50 py-2">
                <p className="font-bold text-red-700">{closedLost}</p>
                <p className="text-xs text-red-600">Lost</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Third row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Pending Approvals */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertCircle className="h-4 w-4 text-orange-500" />
              Pending Approvals
              {approvals.length > 0 && (
                <span className="ml-auto rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
                  {approvals.length}
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {approvals.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 gap-2">
                <CheckCircle className="h-8 w-8 text-green-400" />
                <p className="text-sm text-muted-foreground">No pending approvals</p>
              </div>
            ) : (
              <div className="max-h-72 overflow-y-auto">
                {approvals.map((a) => (
                  <ApprovalRow key={a.id} approval={a} onDecide={handleDecide} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Upcoming deadlines */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Calendar className="h-4 w-4" />
              Upcoming Deadlines
              <span className="ml-auto text-xs font-normal text-muted-foreground">
                Next 30 days
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {deadlines.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 gap-2">
                <Clock className="h-8 w-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">No deadlines in next 30 days</p>
              </div>
            ) : (
              <div className="space-y-0 max-h-72 overflow-y-auto">
                {deadlines.map((deal) => {
                  const daysLeft = deal.due_date
                    ? Math.ceil(
                        (new Date(deal.due_date).getTime() - Date.now()) /
                          86400000
                      )
                    : null;
                  const urgency =
                    daysLeft !== null && daysLeft <= 7
                      ? "text-red-600"
                      : daysLeft !== null && daysLeft <= 14
                      ? "text-yellow-600"
                      : "text-green-600";
                  return (
                    <div
                      key={deal.id}
                      className="flex items-center justify-between border-b py-3 last:border-b-0"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-foreground">
                          {deal.title}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {deal.stage_display}
                        </p>
                      </div>
                      <div className="ml-4 shrink-0 text-right">
                        <p className={`text-sm font-semibold ${urgency}`}>
                          {daysLeft !== null ? `${daysLeft}d` : "--"}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(deal.due_date)}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Proposal breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <FileEdit className="h-4 w-4" />
            Proposal Status Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          {proposals.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">
              No proposals found
            </p>
          ) : (
            <div className="flex flex-wrap gap-4">
              {Object.entries(proposalByStatus).map(([status, count]) => (
                <div
                  key={status}
                  className="flex flex-col items-center rounded-lg border bg-secondary/30 px-6 py-4"
                >
                  <p className="text-2xl font-bold text-foreground">{count}</p>
                  <p className="mt-1 text-xs text-muted-foreground capitalize">
                    {status.replace(/_/g, " ")}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent opportunities */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <TrendingUp className="h-4 w-4" />
            Recent Opportunities
          </CardTitle>
        </CardHeader>
        <CardContent>
          {opportunities.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">
              No recent opportunities
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Title</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Agency</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Score</th>
                    <th className="pb-3 font-medium text-muted-foreground">Posted</th>
                  </tr>
                </thead>
                <tbody>
                  {opportunities.map((opp) => (
                    <tr key={opp.id} className="border-b last:border-b-0">
                      <td className="py-3 pr-4 font-medium">
                        {opp.title.length > 60
                          ? opp.title.slice(0, 60) + "..."
                          : opp.title}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {opp.agency || "--"}
                      </td>
                      <td className="py-3 pr-4">
                        {opp.score ? (
                          <span className="font-medium">
                            {opp.score.total_score.toFixed(0)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">--</span>
                        )}
                      </td>
                      <td className="py-3 text-muted-foreground">
                        {formatDate(opp.posted_date)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
