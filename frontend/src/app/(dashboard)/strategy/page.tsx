"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  getStrategies,
  getStrategicGoals,
  getPortfolioSnapshots,
  createStrategy,
} from "@/services/strategy";
import {
  CompanyStrategy,
  StrategicGoal,
  PortfolioSnapshot,
  GoalCategory,
  GoalStatus,
} from "@/types/strategy";
import {
  Target,
  TrendingUp,
  Loader2,
  RefreshCw,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Plus,
  X,
} from "lucide-react";
import { Input } from "@/components/ui/input";

// ─── helpers ────────────────────────────────────────────────────────────────

const formatCurrency = (value: string | null): string => {
  if (!value) return "--";
  const num = parseFloat(value);
  if (isNaN(num)) return "--";
  if (num >= 1_000_000_000) return `$${(num / 1_000_000_000).toFixed(1)}B`;
  if (num >= 1_000_000) return `$${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `$${(num / 1_000).toFixed(0)}K`;
  return `$${num.toFixed(0)}`;
};

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

const formatPercent = (value: number): string => `${(value * 100).toFixed(0)}%`;

// ─── badge helpers ──────────────────────────────────────────────────────────

const GOAL_CATEGORY_LABELS: Record<GoalCategory, string> = {
  revenue: "Revenue",
  market_entry: "Market Entry",
  market_share: "Market Share",
  capability: "Capability",
  relationship: "Relationship",
  portfolio: "Portfolio",
  profitability: "Profitability",
};

const GOAL_CATEGORY_COLORS: Record<GoalCategory, string> = {
  revenue: "bg-blue-100 text-blue-800",
  market_entry: "bg-purple-100 text-purple-800",
  market_share: "bg-indigo-100 text-indigo-800",
  capability: "bg-cyan-100 text-cyan-800",
  relationship: "bg-pink-100 text-pink-800",
  portfolio: "bg-orange-100 text-orange-800",
  profitability: "bg-green-100 text-green-800",
};

function CategoryBadge({ category }: { category: GoalCategory }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${GOAL_CATEGORY_COLORS[category] ?? "bg-gray-100 text-gray-800"}`}
    >
      {GOAL_CATEGORY_LABELS[category] ?? category}
    </span>
  );
}

function StatusBadge({ status }: { status: GoalStatus }) {
  const configs: Record<GoalStatus, { label: string; icon: React.ReactNode; cls: string }> = {
    on_track: {
      label: "On Track",
      icon: <CheckCircle2 className="h-3 w-3" />,
      cls: "bg-green-100 text-green-800",
    },
    at_risk: {
      label: "At Risk",
      icon: <AlertTriangle className="h-3 w-3" />,
      cls: "bg-yellow-100 text-yellow-800",
    },
    behind: {
      label: "Behind",
      icon: <XCircle className="h-3 w-3" />,
      cls: "bg-red-100 text-red-800",
    },
    achieved: {
      label: "Achieved",
      icon: <CheckCircle2 className="h-3 w-3" />,
      cls: "bg-emerald-100 text-emerald-800",
    },
  };
  const cfg = configs[status] ?? { label: status, icon: null, cls: "bg-gray-100 text-gray-800" };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${cfg.cls}`}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ─── market chip ────────────────────────────────────────────────────────────

function MarketChip({ label, color }: { label: string; color: string }) {
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}

// ─── progress bar ───────────────────────────────────────────────────────────

function ProgressBar({ value, max, color = "bg-blue-500" }: { value: number; max: number; color?: string }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-muted-foreground w-20 text-right">
        {value.toLocaleString()} / {max.toLocaleString()}
      </span>
    </div>
  );
}

// ─── new strategy modal ──────────────────────────────────────────────────────

interface NewStrategyModalProps {
  onClose: () => void;
  onCreated: (strategy: CompanyStrategy) => void;
}

function NewStrategyModal({ onClose, onCreated }: NewStrategyModalProps) {
  const [missionStatement, setMissionStatement] = useState("");
  const [vision3Year, setVision3Year] = useState("");
  const [effectiveDate, setEffectiveDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [targetRevenue, setTargetRevenue] = useState("");
  const [targetWinRate, setTargetWinRate] = useState("30");
  const [targetMargin, setTargetMargin] = useState("12");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!missionStatement.trim()) {
      setError("Mission statement is required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const payload: Partial<CompanyStrategy> = {
        mission_statement: missionStatement.trim(),
        vision_3_year: vision3Year.trim(),
        effective_date: effectiveDate,
        target_win_rate: Number(targetWinRate) / 100,
        target_margin: Number(targetMargin) / 100,
        is_active: true,
      };
      if (targetRevenue.trim()) payload.target_revenue = targetRevenue.trim();
      const newStrategy = await createStrategy(payload);
      onCreated(newStrategy);
    } catch {
      setError("Failed to create strategy. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-lg border bg-background shadow-lg">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">New Strategy</h2>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">
              Mission Statement <span className="text-red-500">*</span>
            </label>
            <textarea
              value={missionStatement}
              onChange={(e) => setMissionStatement(e.target.value)}
              placeholder="e.g. Deliver mission-critical IT solutions to federal agencies..."
              rows={3}
              autoFocus
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">3-Year Vision</label>
            <textarea
              value={vision3Year}
              onChange={(e) => setVision3Year(e.target.value)}
              placeholder="Where the company wants to be in 3 years..."
              rows={2}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Effective Date</label>
            <Input
              type="date"
              value={effectiveDate}
              onChange={(e) => setEffectiveDate(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Target Revenue ($)</label>
              <Input
                value={targetRevenue}
                onChange={(e) => setTargetRevenue(e.target.value)}
                placeholder="e.g. 50000000"
                type="number"
                min="0"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Win Rate (%)</label>
              <Input
                value={targetWinRate}
                onChange={(e) => setTargetWinRate(e.target.value)}
                type="number"
                min="0"
                max="100"
                step="1"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Margin (%)</label>
              <Input
                value={targetMargin}
                onChange={(e) => setTargetMargin(e.target.value)}
                type="number"
                min="0"
                max="100"
                step="1"
              />
            </div>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating...</>
              ) : (
                "Create Strategy"
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── main page ──────────────────────────────────────────────────────────────

export default function StrategyPage() {
  const [strategy, setStrategy] = useState<CompanyStrategy | null>(null);
  const [goals, setGoals] = useState<StrategicGoal[]>([]);
  const [snapshot, setSnapshot] = useState<PortfolioSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewModal, setShowNewModal] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [stratData, snapData] = await Promise.all([
        getStrategies(),
        getPortfolioSnapshots(),
      ]);

      const latest = stratData.results?.[0] ?? null;
      setStrategy(latest);

      if (latest) {
        const goalsData = await getStrategicGoals({ strategy: latest.id });
        setGoals(goalsData.results ?? []);
      }

      setSnapshot(snapData.results?.[0] ?? null);
    } catch (err) {
      setError("Failed to load strategy data. Please try again.");
      console.error("Error fetching strategy:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Company Strategy</h1>
          <p className="text-muted-foreground">
            Active strategic plan driving bid decisions and portfolio management
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            {loading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Refresh
          </Button>
          <Button onClick={() => setShowNewModal(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Strategy
          </Button>
        </div>
      </div>

      {showNewModal && (
        <NewStrategyModal
          onClose={() => setShowNewModal(false)}
          onCreated={(newStrategy) => {
            setStrategy(newStrategy);
            setGoals([]);
            setShowNewModal(false);
          }}
        />
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading strategy data...</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-20">
          <p className="text-red-600 mb-4">{error}</p>
          <Button variant="outline" onClick={fetchData}>
            Retry
          </Button>
        </div>
      ) : !strategy ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Target className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground text-lg">No strategy found.</p>
            <p className="text-muted-foreground text-sm mt-1">
              Create a strategy to start driving intelligent bid decisions.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Active Strategy Card */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-primary" />
                  Active Strategy
                </CardTitle>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    Version {strategy.version}
                  </span>
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                    Active
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-lg bg-muted/40 p-4">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                    Effective Date
                  </p>
                  <p className="text-sm font-semibold">{formatDate(strategy.effective_date)}</p>
                </div>
                <div className="rounded-lg bg-muted/40 p-4">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                    Target Revenue
                  </p>
                  <p className="text-sm font-semibold text-green-700">
                    {formatCurrency(strategy.target_revenue)}
                  </p>
                </div>
                <div className="rounded-lg bg-muted/40 p-4 flex gap-4">
                  <div className="flex-1">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                      Win Rate
                    </p>
                    <p className="text-sm font-semibold text-blue-700">
                      {formatPercent(strategy.target_win_rate)}
                    </p>
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                      Margin
                    </p>
                    <p className="text-sm font-semibold text-purple-700">
                      {formatPercent(strategy.target_margin)}
                    </p>
                  </div>
                </div>
              </div>

              {strategy.mission_statement && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-1">
                    Mission Statement
                  </p>
                  <p className="text-sm leading-relaxed">{strategy.mission_statement}</p>
                </div>
              )}

              {strategy.vision_3_year && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-1">
                    3-Year Vision
                  </p>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {strategy.vision_3_year}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Target Markets */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <TrendingUp className="h-4 w-4 text-primary" />
                Target Markets
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Growth Markets */}
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-green-700 mb-2">
                    Growth Markets
                  </p>
                  {strategy.growth_markets.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {strategy.growth_markets.map((m) => (
                        <MarketChip key={m} label={m} color="bg-green-100 text-green-800" />
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">None defined</p>
                  )}
                </div>

                {/* Mature Markets */}
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-blue-700 mb-2">
                    Mature Markets
                  </p>
                  {strategy.mature_markets.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {strategy.mature_markets.map((m) => (
                        <MarketChip key={m} label={m} color="bg-blue-100 text-blue-800" />
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">None defined</p>
                  )}
                </div>

                {/* Exit Markets */}
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-red-700 mb-2">
                    Exit Markets
                  </p>
                  {strategy.exit_markets.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {strategy.exit_markets.map((m) => (
                        <MarketChip key={m} label={m} color="bg-red-100 text-red-800" />
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">None defined</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Strategic Goals */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">
                Strategic Goals
                {goals.length > 0 && (
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    ({goals.length})
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {goals.length === 0 ? (
                <p className="text-sm text-muted-foreground py-4 text-center">
                  No strategic goals defined for this strategy.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">Goal</th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">Category</th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">Metric</th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground min-w-[200px]">
                          Progress
                        </th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">Deadline</th>
                        <th className="pb-3 font-medium text-muted-foreground">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {goals.map((goal) => (
                        <tr key={goal.id} className="border-b">
                          <td className="py-3 pr-4 font-medium">{goal.name}</td>
                          <td className="py-3 pr-4">
                            <CategoryBadge category={goal.category} />
                          </td>
                          <td className="py-3 pr-4 text-muted-foreground">{goal.metric}</td>
                          <td className="py-3 pr-4">
                            <ProgressBar
                              value={goal.current_value}
                              max={goal.target_value}
                              color={
                                goal.status === "behind"
                                  ? "bg-red-500"
                                  : goal.status === "at_risk"
                                  ? "bg-yellow-500"
                                  : "bg-green-500"
                              }
                            />
                          </td>
                          <td className="py-3 pr-4 text-muted-foreground">
                            {formatDate(goal.deadline)}
                          </td>
                          <td className="py-3">
                            <StatusBadge status={goal.status} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Portfolio Snapshot + Win Themes + Differentiators */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Portfolio Snapshot */}
            <div className="lg:col-span-2">
              <Card className="h-full">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Portfolio Snapshot</CardTitle>
                </CardHeader>
                <CardContent>
                  {!snapshot ? (
                    <p className="text-sm text-muted-foreground py-4 text-center">
                      No portfolio snapshot available.
                    </p>
                  ) : (
                    <div className="space-y-5">
                      {/* Stats row */}
                      <div className="grid grid-cols-3 gap-4">
                        <div className="rounded-lg bg-muted/40 p-3 text-center">
                          <p className="text-2xl font-bold">{snapshot.active_deals}</p>
                          <p className="text-xs text-muted-foreground">Active Deals</p>
                        </div>
                        <div className="rounded-lg bg-muted/40 p-3 text-center">
                          <p className="text-2xl font-bold text-green-700">
                            {formatCurrency(snapshot.total_pipeline_value)}
                          </p>
                          <p className="text-xs text-muted-foreground">Pipeline Value</p>
                        </div>
                        <div className="rounded-lg bg-muted/40 p-3 text-center">
                          <p className="text-2xl font-bold text-blue-700">
                            {(snapshot.strategic_alignment_score * 100).toFixed(0)}%
                          </p>
                          <p className="text-xs text-muted-foreground">Alignment Score</p>
                        </div>
                      </div>

                      {/* Capacity utilization */}
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-xs font-medium text-muted-foreground">
                            Capacity Utilization
                          </p>
                          <p className="text-xs font-semibold">
                            {(snapshot.capacity_utilization * 100).toFixed(0)}%
                          </p>
                        </div>
                        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              snapshot.capacity_utilization > 0.85
                                ? "bg-red-500"
                                : snapshot.capacity_utilization > 0.65
                                ? "bg-yellow-500"
                                : "bg-green-500"
                            }`}
                            style={{
                              width: `${Math.min(snapshot.capacity_utilization * 100, 100)}%`,
                            }}
                          />
                        </div>
                      </div>

                      {/* AI Recommendations */}
                      {snapshot.ai_recommendations &&
                        snapshot.ai_recommendations.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                              AI Recommendations
                            </p>
                            <ul className="space-y-1.5">
                              {snapshot.ai_recommendations.map((rec, idx) => (
                                <li key={idx} className="flex items-start gap-2 text-sm">
                                  <ChevronRight className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                                  <span>{rec}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                      <p className="text-xs text-muted-foreground">
                        Snapshot date: {formatDate(snapshot.snapshot_date)}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Win Themes & Differentiators */}
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Win Themes</CardTitle>
                </CardHeader>
                <CardContent>
                  {strategy.win_themes.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No win themes defined.</p>
                  ) : (
                    <ol className="space-y-2">
                      {strategy.win_themes.map((theme, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <span className="flex-shrink-0 flex items-center justify-center h-5 w-5 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                            {idx + 1}
                          </span>
                          <span>{theme}</span>
                        </li>
                      ))}
                    </ol>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Differentiators</CardTitle>
                </CardHeader>
                <CardContent>
                  {strategy.differentiators.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No differentiators defined.</p>
                  ) : (
                    <ul className="space-y-2">
                      {strategy.differentiators.map((diff, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <span className="text-primary font-bold mt-0.5">•</span>
                          <span>{diff}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
