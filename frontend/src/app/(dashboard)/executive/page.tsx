"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  getExecutiveDashboard,
  getPipelineLoad,
  ExecutiveDashboardData,
  PipelineLoad,
} from "@/services/executive";
import {
  Loader2,
  RefreshCw,
  Target,
  DollarSign,
  FileText,
  ClipboardCheck,
  TrendingUp,
  AlertCircle,
  ArrowRight,
  BarChart3,
} from "lucide-react";

const formatValue = (v: number | string | null | undefined): string => {
  const n = Number(v) || 0;
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
};

const STAGE_LABELS: Record<string, string> = {
  intake: "Intake",
  qualify: "Qualify",
  bid_no_bid: "Bid/No-Bid",
  capture_plan: "Capture Plan",
  proposal_dev: "Proposal Dev",
  red_team: "Red Team",
  final_review: "Final Review",
  submit: "Submit",
  post_submit: "Post Submit",
  award_pending: "Award Pending",
  contract_setup: "Contract Setup",
  delivery: "Delivery",
};

const STAGE_COLORS: Record<string, string> = {
  intake: "bg-gray-400",
  qualify: "bg-blue-400",
  bid_no_bid: "bg-yellow-400",
  capture_plan: "bg-orange-400",
  proposal_dev: "bg-purple-400",
  red_team: "bg-red-400",
  final_review: "bg-orange-500",
  submit: "bg-green-400",
  post_submit: "bg-teal-400",
  award_pending: "bg-yellow-500",
  contract_setup: "bg-blue-500",
  delivery: "bg-green-500",
};

export default function ExecutiveDashboardPage() {
  const [data, setData] = useState<ExecutiveDashboardData | null>(null);
  const [pipelineLoad, setPipelineLoad] = useState<PipelineLoad | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const [dashboard, load] = await Promise.all([
        getExecutiveDashboard(),
        getPipelineLoad(),
      ]);
      setData(dashboard);
      setPipelineLoad(load);
    } catch {
      setError("Failed to load executive dashboard data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">Loading executive dashboard...</span>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <AlertCircle className="h-10 w-10 text-red-500 mb-4" />
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={() => loadData()}>
          <RefreshCw className="mr-2 h-4 w-4" /> Retry
        </Button>
      </div>
    );
  }

  const summary = data?.summary;
  const funnel = data?.pipeline_funnel;
  const forecast = data?.revenue_forecast || [];
  const winTrend = data?.win_rate_trend || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Executive Dashboard
          </h1>
          <p className="text-muted-foreground">
            Strategic overview of pipeline health, forecasts, and win rates
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => loadData(true)}
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

      {/* Top KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Deals</p>
                <p className="text-3xl font-bold">{summary?.active_deals ?? 0}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {summary?.pending_approvals ?? 0} pending approvals
                </p>
              </div>
              <Target className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pipeline Value</p>
                <p className="text-3xl font-bold">{formatValue(summary?.pipeline_value ?? 0)}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Weighted: {formatValue(pipelineLoad?.weighted_pipeline_value ?? pipelineLoad?.total_pipeline_value ?? 0)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Win Rate</p>
                <p className="text-3xl font-bold">
                  {summary?.win_rate != null ? `${Number(summary.win_rate).toFixed(0)}%` : "--"}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {summary?.closed_won ?? 0}W / {summary?.closed_lost ?? 0}L
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Contracts</p>
                <p className="text-3xl font-bold">{summary?.active_contracts ?? 0}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {summary?.proposals_in_progress ?? 0} proposals in progress
                </p>
              </div>
              <ClipboardCheck className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline Funnel */}
      {funnel && Object.keys(funnel.stages || {}).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-muted-foreground" />
              Pipeline Funnel
              <span className="ml-auto text-sm font-normal text-muted-foreground">
                {funnel.total_active} active deals
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(funnel.stages)
                .filter(([, count]) => count > 0)
                .map(([stage, count]) => {
                  const maxCount = Math.max(...Object.values(funnel.stages), 1);
                  const barWidth = Math.round((count / maxCount) * 100);
                  return (
                    <div key={stage} className="flex items-center gap-3">
                      <span className="text-xs font-medium w-28 text-right shrink-0">
                        {STAGE_LABELS[stage] || stage}
                      </span>
                      <div className="flex-1 h-6 rounded bg-muted overflow-hidden relative">
                        <div
                          className={`h-full rounded transition-all duration-500 ${STAGE_COLORS[stage] || "bg-gray-400"}`}
                          style={{ width: `${barWidth}%` }}
                        />
                        <span className="absolute inset-0 flex items-center px-2 text-xs font-semibold">
                          {count}
                        </span>
                      </div>
                    </div>
                  );
                })}
            </div>

            {/* Conversion Rates */}
            {Object.keys(funnel.conversion_rates || {}).length > 0 && (
              <div className="mt-6 pt-4 border-t">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Stage Conversion Rates
                </p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(funnel.conversion_rates).map(([transition, rate]) => {
                    const [from, to] = transition.split("_to_");
                    return (
                      <div
                        key={transition}
                        className="inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs"
                      >
                        <span className="text-muted-foreground">{STAGE_LABELS[from] || from}</span>
                        <ArrowRight className="h-3 w-3 text-muted-foreground" />
                        <span className="text-muted-foreground">{STAGE_LABELS[to] || to}</span>
                        <span className={`font-bold ml-1 ${Number(rate) >= 70 ? "text-green-600" : Number(rate) >= 40 ? "text-yellow-600" : "text-red-600"}`}>
                          {Number(rate).toFixed(0)}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Revenue Forecast */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-muted-foreground" />
              Revenue Forecast
            </CardTitle>
          </CardHeader>
          <CardContent>
            {forecast.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No forecast data available yet.
              </p>
            ) : (
              <div className="space-y-4">
                {forecast.map((q) => {
                  const maxVal = Math.max(...forecast.map((f) => Number(f.pipeline_value) || 0), 1);
                  const pipelineWidth = Math.round(((Number(q.pipeline_value) || 0) / maxVal) * 100);
                  const weightedWidth = Math.round(((Number(q.weighted_value) || 0) / maxVal) * 100);
                  return (
                    <div key={q.quarter} className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{q.quarter}</span>
                        <span className="text-xs text-muted-foreground">{q.deal_count} deals</span>
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground w-16">Pipeline</span>
                          <div className="flex-1 h-3 rounded-full bg-muted overflow-hidden">
                            <div className="h-full rounded-full bg-blue-300" style={{ width: `${pipelineWidth}%` }} />
                          </div>
                          <span className="text-xs font-medium w-16 text-right">{formatValue(q.pipeline_value)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground w-16">Weighted</span>
                          <div className="flex-1 h-3 rounded-full bg-muted overflow-hidden">
                            <div className="h-full rounded-full bg-green-400" style={{ width: `${weightedWidth}%` }} />
                          </div>
                          <span className="text-xs font-medium w-16 text-right">{formatValue(q.weighted_value)}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
                <div className="flex gap-4 pt-2 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-blue-300 inline-block" /> Pipeline Value</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-400 inline-block" /> Probability-Weighted</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Win Rate Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-muted-foreground" />
              Win Rate Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            {winTrend.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No win/loss data available yet.
              </p>
            ) : (
              <div className="space-y-3">
                {winTrend.map((m) => (
                  <div key={m.month} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium">{m.month}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-green-600">{m.won}W</span>
                        <span className="text-red-600">{m.lost}L</span>
                        <span className={`font-bold ${Number(m.win_rate) >= 50 ? "text-green-600" : Number(m.win_rate) > 0 ? "text-yellow-600" : "text-muted-foreground"}`}>
                          {m.total > 0 ? `${Number(m.win_rate).toFixed(0)}%` : "--"}
                        </span>
                      </div>
                    </div>
                    <div className="h-4 rounded-full bg-muted overflow-hidden flex">
                      {m.total > 0 && (
                        <>
                          <div
                            className="h-full bg-green-400"
                            style={{ width: `${(m.won / m.total) * 100}%` }}
                            title={`Won: ${m.won}`}
                          />
                          <div
                            className="h-full bg-red-300"
                            style={{ width: `${(m.lost / m.total) * 100}%` }}
                            title={`Lost: ${m.lost}`}
                          />
                        </>
                      )}
                    </div>
                    {m.moving_avg != null && (
                      <p className="text-xs text-muted-foreground">
                        3-month avg: {Number(m.moving_avg).toFixed(0)}%
                      </p>
                    )}
                  </div>
                ))}
                <div className="flex gap-4 pt-2 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-400 inline-block" /> Won</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-300 inline-block" /> Lost</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Pipeline Load */}
      {pipelineLoad && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="h-5 w-5 text-muted-foreground" />
              Pipeline Load
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="rounded-lg border p-3 text-center">
                <p className="text-xs text-muted-foreground">Active Deals</p>
                <p className="text-2xl font-bold">{pipelineLoad.active_deal_count ?? pipelineLoad.total_active_deals ?? 0}</p>
              </div>
              <div className="rounded-lg border p-3 text-center">
                <p className="text-xs text-muted-foreground">In Proposal Stage</p>
                <p className="text-2xl font-bold">{pipelineLoad.proposal_stage_count ?? (pipelineLoad.by_stage?.proposal_dev ?? 0)}</p>
              </div>
              <div className="rounded-lg border p-3 text-center">
                <p className="text-xs text-muted-foreground">Total Pipeline</p>
                <p className="text-2xl font-bold">{formatValue(pipelineLoad.total_pipeline_value ?? 0)}</p>
              </div>
              <div className="rounded-lg border p-3 text-center">
                <p className="text-xs text-muted-foreground">Avg Per Stage</p>
                <p className="text-2xl font-bold">{pipelineLoad.weighted_pipeline_value ? formatValue(pipelineLoad.weighted_pipeline_value) : (pipelineLoad.avg_per_stage ?? 0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
