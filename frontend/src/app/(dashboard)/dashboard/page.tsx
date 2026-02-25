"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  TrendingUp,
  DollarSign,
  FileText,
  Target,
  CheckCircle,
  Star,
  RefreshCw,
  Loader2,
  AlertCircle,
  Clock,
} from "lucide-react";
import {
  fetchDashboardSnapshot,
  DashboardSnapshot,
} from "@/services/dashboard";
import { decideApproval, PendingApproval, PipelineStageCount } from "@/services/analytics";
import { Deal, DealStage } from "@/types/deal";
import { Opportunity } from "@/types/opportunity";

// ── Helpers ────────────────────────────────────────────────────────────────

const formatValue = (v: number): string => {
  if (v >= 1_000_000_000) return `$${(v / 1_000_000_000).toFixed(1)}B`;
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${v}`;
};

const timeAgo = (date: string): string => {
  const diff = Date.now() - new Date(date).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return "Just now";
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
};

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

const daysUntil = (dateStr: string): number => {
  return Math.ceil(
    (new Date(dateStr).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  );
};

const formatApprovalType = (type: string): string => {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
};

const getUserDisplayName = (
  detail: PendingApproval["requested_by_detail"]
): string => {
  if (!detail) return "--";
  const full = `${detail.first_name} ${detail.last_name}`.trim();
  return full || detail.username;
};

// ── Stage config ───────────────────────────────────────────────────────────

const STAGE_LABELS: Partial<Record<DealStage, string>> = {
  intake: "Intake",
  qualify: "Qualify",
  bid_no_bid: "Bid / No-Bid",
  capture_plan: "Capture Plan",
  proposal_dev: "Proposal Dev",
  red_team: "Red Team",
  final_review: "Final Review",
  submit: "Submit",
  post_submit: "Post Submit",
  award_pending: "Award Pending",
  contract_setup: "Contract Setup",
  delivery: "Delivery",
  closed_won: "Closed Won",
  closed_lost: "Closed Lost",
  no_bid: "No Bid",
};

const STAGE_TEXT_COLORS: Partial<Record<DealStage, string>> = {
  intake: "text-gray-600 bg-gray-100",
  qualify: "text-blue-700 bg-blue-100",
  bid_no_bid: "text-yellow-700 bg-yellow-100",
  capture_plan: "text-orange-700 bg-orange-100",
  proposal_dev: "text-purple-700 bg-purple-100",
  red_team: "text-red-700 bg-red-100",
  final_review: "text-orange-700 bg-orange-100",
  submit: "text-green-700 bg-green-100",
  post_submit: "text-teal-700 bg-teal-100",
  award_pending: "text-yellow-700 bg-yellow-100",
  contract_setup: "text-blue-700 bg-blue-100",
  delivery: "text-green-700 bg-green-100",
  closed_won: "text-emerald-700 bg-emerald-100",
  closed_lost: "text-gray-600 bg-gray-100",
  no_bid: "text-slate-600 bg-slate-100",
};

const PIPELINE_BAR_COLORS: Partial<Record<DealStage, string>> = {
  intake: "bg-gray-400",
  qualify: "bg-blue-400",
  bid_no_bid: "bg-yellow-400",
  capture_plan: "bg-orange-400",
  proposal_dev: "bg-purple-400",
  red_team: "bg-red-400",
  final_review: "bg-orange-500",
  submit: "bg-green-400",
};

const PRIORITY_COLORS: Record<number, string> = {
  1: "text-red-700 bg-red-100",
  2: "text-orange-700 bg-orange-100",
  3: "text-blue-700 bg-blue-100",
  4: "text-gray-600 bg-gray-100",
};

const PRIORITY_LABELS: Record<number, string> = {
  1: "Critical",
  2: "High",
  3: "Medium",
  4: "Low",
};

// ── Loading Skeleton ───────────────────────────────────────────────────────

function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded bg-muted ${className ?? "h-4 w-full"}`}
    />
  );
}

function KpiSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <SkeletonBlock className="h-4 w-28" />
            <SkeletonBlock className="h-5 w-5 rounded-full" />
          </CardHeader>
          <CardContent>
            <SkeletonBlock className="h-8 w-20 mb-2" />
            <SkeletonBlock className="h-3 w-32" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ── KPI Cards ──────────────────────────────────────────────────────────────

interface KpiCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
  iconColor: string;
  badge?: React.ReactNode;
}

function KpiCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor,
  badge,
}: KpiCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="flex items-center gap-1.5">
          {badge}
          <Icon className={`h-5 w-5 ${iconColor}`} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </CardContent>
    </Card>
  );
}

// ── Pipeline Distribution ──────────────────────────────────────────────────

function PipelineDistribution({
  distribution,
}: {
  distribution: PipelineStageCount[];
}) {
  const maxCount = Math.max(...distribution.map((d) => d.count), 1);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Pipeline Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {distribution.map(({ stage, count }) => {
            const barWidth = Math.round((count / maxCount) * 100);
            const barColor =
              PIPELINE_BAR_COLORS[stage] ?? "bg-gray-300";
            const labelColor =
              STAGE_TEXT_COLORS[stage] ?? "text-gray-600 bg-gray-100";
            return (
              <div key={stage} className="flex items-center gap-3">
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded shrink-0 w-28 text-center ${labelColor}`}
                >
                  {STAGE_LABELS[stage] ?? stage}
                </span>
                <span className="text-xs text-muted-foreground w-5 text-right shrink-0">
                  {count}
                </span>
                <div className="flex-1 h-2.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Recent Activity Feed ───────────────────────────────────────────────────

function RecentActivityFeed({ deals }: { deals: Deal[] }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Recent Activity</CardTitle>
        <Link
          href="/deals"
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          View all
        </Link>
      </CardHeader>
      <CardContent>
        {deals.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No recent activity.
          </p>
        ) : (
          <div className="space-y-3">
            {deals.map((deal) => {
              const stageColor =
                STAGE_TEXT_COLORS[deal.stage] ?? "text-gray-600 bg-gray-100";
              const priorityColor = PRIORITY_COLORS[deal.priority] ?? PRIORITY_COLORS[3];
              return (
                <div
                  key={deal.id}
                  className="flex items-start justify-between gap-3 py-2 border-b border-border last:border-0"
                >
                  <div className="min-w-0 flex-1">
                    <Link
                      href="/deals"
                      className="text-sm font-medium hover:underline line-clamp-1"
                    >
                      {deal.title}
                    </Link>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      <span
                        className={`text-xs font-medium px-1.5 py-0.5 rounded ${stageColor}`}
                      >
                        {STAGE_LABELS[deal.stage] ?? deal.stage}
                      </span>
                      <span
                        className={`text-xs font-medium px-1.5 py-0.5 rounded ${priorityColor}`}
                      >
                        {PRIORITY_LABELS[deal.priority] ?? deal.priority_display}
                      </span>
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0 mt-0.5">
                    {timeAgo(deal.updated_at)}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Upcoming Deadlines ─────────────────────────────────────────────────────

function UpcomingDeadlines({ deals }: { deals: Deal[] }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Upcoming Deadlines</CardTitle>
        <Clock className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        {deals.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No deadlines in the next 30 days.
          </p>
        ) : (
          <div className="space-y-3">
            {deals.map((deal) => {
              const days = daysUntil(deal.due_date!);
              const daysColor =
                days <= 7
                  ? "text-red-600 font-semibold"
                  : days <= 30
                  ? "text-yellow-600 font-medium"
                  : "text-green-600";
              const stageColor =
                STAGE_TEXT_COLORS[deal.stage] ?? "text-gray-600 bg-gray-100";
              return (
                <div
                  key={deal.id}
                  className="flex items-center justify-between gap-3 py-2 border-b border-border last:border-0"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium line-clamp-1">
                      {deal.title}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-muted-foreground">
                        {formatDate(deal.due_date)}
                      </span>
                      <span
                        className={`text-xs font-medium px-1.5 py-0.5 rounded ${stageColor}`}
                      >
                        {STAGE_LABELS[deal.stage] ?? deal.stage}
                      </span>
                    </div>
                  </div>
                  <span className={`text-xs shrink-0 ${daysColor}`}>
                    {days}d
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Pending Approvals Panel ────────────────────────────────────────────────

interface PendingApprovalsPanelProps {
  approvals: PendingApproval[];
  onDecide: (
    id: string,
    decision: "approved" | "rejected"
  ) => Promise<void>;
}

function PendingApprovalsPanel({
  approvals,
  onDecide,
}: PendingApprovalsPanelProps) {
  const [deciding, setDeciding] = useState<Record<string, boolean>>({});

  const handleDecide = async (
    id: string,
    decision: "approved" | "rejected"
  ) => {
    setDeciding((prev) => ({ ...prev, [id]: true }));
    try {
      await onDecide(id, decision);
    } finally {
      setDeciding((prev) => ({ ...prev, [id]: false }));
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Pending Approvals</CardTitle>
        {approvals.length > 0 && (
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700">
            {approvals.length} pending
          </span>
        )}
      </CardHeader>
      <CardContent>
        {approvals.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No pending approvals.
          </p>
        ) : (
          <div className="space-y-3">
            {approvals.map((approval) => {
              const isDeciding = deciding[approval.id] ?? false;
              return (
                <div
                  key={approval.id}
                  className="rounded-lg border border-border p-3 space-y-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium line-clamp-1">
                        {approval.deal_title ?? "Deal"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatApprovalType(approval.approval_type)}
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground shrink-0">
                      {timeAgo(approval.created_at)}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                    <div>
                      <span className="font-medium text-foreground">
                        Requested by:
                      </span>{" "}
                      {getUserDisplayName(approval.requested_by_detail)}
                    </div>
                    <div>
                      <span className="font-medium text-foreground">
                        Requested from:
                      </span>{" "}
                      {getUserDisplayName(approval.requested_from_detail)}
                    </div>
                  </div>

                  {approval.ai_recommendation && (
                    <p className="text-xs text-muted-foreground italic line-clamp-2">
                      AI: {approval.ai_recommendation}
                    </p>
                  )}

                  <div className="flex gap-2 pt-1">
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1 h-7 text-xs border-green-300 text-green-700 hover:bg-green-50"
                      disabled={isDeciding}
                      onClick={() => handleDecide(approval.id, "approved")}
                    >
                      {isDeciding ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        "Approve"
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1 h-7 text-xs border-red-300 text-red-700 hover:bg-red-50"
                      disabled={isDeciding}
                      onClick={() => handleDecide(approval.id, "rejected")}
                    >
                      {isDeciding ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        "Reject"
                      )}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Recent Opportunities ───────────────────────────────────────────────────

function RecentOpportunities({ opportunities }: { opportunities: Opportunity[] }) {
  const truncate = (str: string, max: number) =>
    str && str.length > max ? str.slice(0, max) + "…" : str;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Recent Opportunities</CardTitle>
        <Link
          href="/opportunities"
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          View all
        </Link>
      </CardHeader>
      <CardContent>
        {opportunities.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No opportunities found.
          </p>
        ) : (
          <div className="space-y-3">
            {opportunities.map((opp) => {
              const score = opp.score?.total_score;
              const deadline = opp.response_deadline
                ? formatDate(opp.response_deadline)
                : "--";
              return (
                <div
                  key={opp.id}
                  className="py-2 border-b border-border last:border-0 space-y-1"
                >
                  <Link
                    href={`/opportunities/${opp.id}`}
                    className="text-sm font-medium hover:underline line-clamp-2"
                  >
                    {truncate(opp.title, 80)}
                  </Link>
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="text-xs text-muted-foreground">
                      {truncate(opp.agency, 40)}
                    </span>
                    <div className="flex items-center gap-2">
                      {typeof score === "number" && (
                        <span className="text-xs font-semibold px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">
                          {score.toFixed(0)}
                        </span>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {deadline}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Main Dashboard Page ────────────────────────────────────────────────────

export default function DashboardPage() {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadDashboard = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const data = await fetchDashboardSnapshot();
      setSnapshot(data);
    } catch (err) {
      console.error("[DashboardPage] Failed to load dashboard:", err);
      setError("Failed to load dashboard data. Please try again.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const handleApprovalDecide = async (
    id: string,
    decision: "approved" | "rejected"
  ) => {
    await decideApproval(id, decision);
    // Remove the approval from local state immediately
    setSnapshot((prev) => {
      if (!prev) return prev;
      const updated = prev.pendingApprovals.filter((a) => a.id !== id);
      return {
        ...prev,
        pendingApprovals: updated,
        kpis: { ...prev.kpis, pendingApprovals: updated.length },
      };
    });
  };

  // ── Loading state ────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <div className="animate-pulse h-9 w-48 bg-muted rounded mb-2" />
          <div className="animate-pulse h-4 w-72 bg-muted rounded" />
        </div>
        <KpiSkeleton />
        <div className="grid gap-4 lg:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <SkeletonBlock className="h-5 w-40" />
              </CardHeader>
              <CardContent className="space-y-3">
                {Array.from({ length: 3 }).map((_, j) => (
                  <SkeletonBlock key={j} className="h-10 w-full" />
                ))}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // ── Error state ──────────────────────────────────────────────────────────

  if (error && !snapshot) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your deal management pipeline
          </p>
        </div>
        <div className="flex flex-col items-center justify-center py-24">
          <AlertCircle className="h-10 w-10 text-red-500 mb-4" />
          <p className="text-red-600 mb-4 text-center">{error}</p>
          <Button onClick={() => loadDashboard()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const kpis = snapshot?.kpis;
  const distribution = snapshot?.pipelineDistribution ?? [];
  const recentActivity = snapshot?.recentActivity ?? [];
  const deadlines = snapshot?.upcomingDeadlines ?? [];
  const pendingApprovals = snapshot?.pendingApprovals ?? [];
  const recentOpps = snapshot?.recentOpportunities ?? [];

  // ── KPI card definitions ─────────────────────────────────────────────────

  const kpiCards: KpiCardProps[] = [
    {
      title: "Active Deals",
      value: String(kpis?.activeDeals ?? 0),
      subtitle: "Deals in active pipeline stages",
      icon: Target,
      iconColor: "text-blue-600",
    },
    {
      title: "Pipeline Value",
      value: kpis ? formatValue(kpis.pipelineValue) : "$0",
      subtitle: "Sum of active deal estimated values",
      icon: DollarSign,
      iconColor: "text-green-600",
    },
    {
      title: "Open Proposals",
      value: String(kpis?.openProposals ?? 0),
      subtitle: "Proposals not yet submitted",
      icon: FileText,
      iconColor: "text-orange-600",
    },
    {
      title: "Win Rate",
      value:
        kpis?.winRate !== null && kpis?.winRate !== undefined
          ? `${kpis.winRate.toFixed(0)}%`
          : "--",
      subtitle: "Closed-won vs closed-lost deals",
      icon: TrendingUp,
      iconColor: "text-emerald-600",
    },
    {
      title: "Pending Approvals",
      value: String(kpis?.pendingApprovals ?? 0),
      subtitle: "HITL approvals awaiting decision",
      icon: CheckCircle,
      iconColor:
        (kpis?.pendingApprovals ?? 0) > 0
          ? "text-yellow-600"
          : "text-purple-600",
      badge:
        (kpis?.pendingApprovals ?? 0) > 0 ? (
          <span className="text-xs font-semibold px-1.5 py-0.5 rounded-full bg-yellow-100 text-yellow-700">
            Urgent
          </span>
        ) : undefined,
    },
    {
      title: "Avg Fit Score",
      value:
        kpis?.avgFitScore !== null && kpis?.avgFitScore !== undefined
          ? kpis.avgFitScore.toFixed(1)
          : "--",
      subtitle: "Average composite score for active deals",
      icon: Star,
      iconColor: "text-cyan-600",
    },
  ];

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your deal management pipeline
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => loadDashboard(true)}
          disabled={refreshing}
        >
          {refreshing ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Refresh
        </Button>
      </div>

      {/* Partial error banner */}
      {error && snapshot && (
        <div className="flex items-center gap-2 text-sm text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2.5">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error} — showing last available data.</span>
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto h-7 text-xs"
            onClick={() => loadDashboard(true)}
          >
            Retry
          </Button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {kpiCards.map((kpi) => (
          <KpiCard key={kpi.title} {...kpi} />
        ))}
      </div>

      {/* Pipeline Distribution */}
      <PipelineDistribution distribution={distribution} />

      {/* Activity + Deadlines */}
      <div className="grid gap-4 lg:grid-cols-2">
        <RecentActivityFeed deals={recentActivity} />
        <UpcomingDeadlines deals={deadlines} />
      </div>

      {/* Approvals + Opportunities */}
      <div className="grid gap-4 lg:grid-cols-2">
        <PendingApprovalsPanel
          approvals={pendingApprovals}
          onDecide={handleApprovalDecide}
        />
        <RecentOpportunities opportunities={recentOpps} />
      </div>

      {/* Footer timestamp */}
      {snapshot && (
        <p className="text-xs text-muted-foreground text-right">
          Last updated: {snapshot.fetchedAt.toLocaleTimeString()}
        </p>
      )}
    </div>
  );
}
