"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getRateCards,
  getScenarios,
  getLOEEstimates,
  getPricingApprovals,
  createScenario,
} from "@/services/pricing";
import {
  RateCard,
  PricingScenario,
  LOEEstimate,
  PricingApproval,
} from "@/types/pricing";
import { fetchAllDeals } from "@/services/analytics";
import { Deal } from "@/types/deal";
import {
  Loader2,
  Plus,
  DollarSign,
  TrendingUp,
  CheckCircle,
  BarChart3,
  X,
} from "lucide-react";

type ActiveTab = "scenarios" | "rate-cards" | "loe-estimates";

const STRATEGY_TYPE_LABELS: Record<string, string> = {
  max_profit: "Maximum Profit",
  value_based: "Value-Based",
  competitive: "Competitive",
  aggressive: "Aggressive",
  incumbent_match: "Incumbent Match",
  budget_fit: "Budget Fit",
  floor: "Floor",
};

function toNum(value: string | number | null | undefined): number {
  if (value == null) return 0;
  const n = typeof value === "string" ? parseFloat(value) : value;
  return isNaN(n) ? 0 : n;
}

function formatCurrency(value: string | number | null | undefined): string {
  if (value == null) return "--";
  const n = toNum(value);
  if (n === 0 && value !== 0 && value !== "0") return "--";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// ── New Scenario Modal ────────────────────────────────────────────────────

interface NewScenarioModalProps {
  onClose: () => void;
  onCreated: (scenario: PricingScenario) => void;
}

function NewScenarioModal({ onClose, onCreated }: NewScenarioModalProps) {
  const [name, setName] = useState("");
  const [strategyType, setStrategyType] = useState("competitive");
  const [dealId, setDealId] = useState("");
  const [deals, setDeals] = useState<Deal[]>([]);
  const [dealsLoading, setDealsLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const strategyTypes = [
    { value: "max_profit", label: "Maximum Profit" },
    { value: "value_based", label: "Value-Based" },
    { value: "competitive", label: "Competitive" },
    { value: "aggressive", label: "Aggressive" },
    { value: "incumbent_match", label: "Incumbent Match" },
    { value: "budget_fit", label: "Budget Fit" },
    { value: "floor", label: "Floor" },
  ];

  useEffect(() => {
    fetchAllDeals()
      .then((d) => setDeals(d))
      .catch(() => {})
      .finally(() => setDealsLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !dealId) {
      setError("Name and deal are required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const scenario = await createScenario({ name: name.trim(), strategy_type: strategyType as PricingScenario["strategy_type"], deal: dealId });
      onCreated(scenario);
    } catch {
      setError("Failed to create scenario. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border bg-background shadow-lg">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">New Pricing Scenario</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Scenario Name <span className="text-red-500">*</span></label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Base Scenario – FFP" autoFocus />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Strategy Type</label>
            <select value={strategyType} onChange={(e) => setStrategyType(e.target.value)} className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
              {strategyTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Deal <span className="text-red-500">*</span></label>
            {dealsLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground py-2"><Loader2 className="h-4 w-4 animate-spin" />Loading deals...</div>
            ) : (
              <select value={dealId} onChange={(e) => setDealId(e.target.value)} className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
                <option value="">Select a deal...</option>
                {deals.map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}
              </select>
            )}
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>Cancel</Button>
            <Button type="submit" disabled={submitting || dealsLoading}>
              {submitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating...</> : "Create Scenario"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

export default function PricingPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("scenarios");
  const [showNewModal, setShowNewModal] = useState(false);

  // Data state
  const [scenarios, setScenarios] = useState<PricingScenario[]>([]);
  const [rateCards, setRateCards] = useState<RateCard[]>([]);
  const [loeEstimates, setLoeEstimates] = useState<LOEEstimate[]>([]);
  const [approvals, setApprovals] = useState<PricingApproval[]>([]);

  // UI state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] =
    useState<PricingScenario | null>(null);
  const [scenarioLOEs, setScenarioLOEs] = useState<LOEEstimate[]>([]);
  const [loadingLOEs, setLoadingLOEs] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [scenariosData, rateCardsData, approvalsData] = await Promise.all([
        getScenarios(),
        getRateCards(),
        getPricingApprovals(),
      ]);
      setScenarios(scenariosData.results || []);
      setRateCards(rateCardsData.results || []);
      setApprovals(approvalsData.results || []);
    } catch (err) {
      setError("Failed to load pricing data. Please try again.");
      console.error("Error fetching pricing data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchLOEEstimates = useCallback(async () => {
    try {
      const data = await getLOEEstimates();
      setLoeEstimates(data.results || []);
    } catch (err) {
      console.error("Error fetching LOE estimates:", err);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (activeTab === "loe-estimates") {
      fetchLOEEstimates();
    }
  }, [activeTab, fetchLOEEstimates]);

  const handleScenarioClick = async (scenario: PricingScenario) => {
    setSelectedScenario(scenario);
    setLoadingLOEs(true);
    try {
      const data = await getLOEEstimates({ deal: scenario.deal });
      setScenarioLOEs(data.results || []);
    } catch (err) {
      console.error("Error fetching scenario LOEs:", err);
      setScenarioLOEs([]);
    } finally {
      setLoadingLOEs(false);
    }
  };

  // Computed summary stats
  const recommendedScenarios = scenarios.filter((s) => s.is_recommended);
  const totalPipelineValue = scenarios.reduce(
    (sum, s) => sum + toNum(s.total_price),
    0
  );
  const avgMargin =
    scenarios.length > 0
      ? scenarios.reduce((sum, s) => sum + toNum(s.margin_pct), 0) /
        scenarios.length
      : 0;

  const getApprovalStatus = (scenarioId: string) => {
    const approval = approvals.find((a) => a.scenario === scenarioId);
    return approval?.status || null;
  };

  const tabs: { key: ActiveTab; label: string }[] = [
    { key: "scenarios", label: "Scenarios" },
    { key: "rate-cards", label: "Rate Cards" },
    { key: "loe-estimates", label: "LOE Estimates" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Pricing & Staffing
          </h1>
          <p className="text-muted-foreground">
            Manage pricing scenarios, rate cards, and level-of-effort estimates
          </p>
        </div>
        <Button onClick={() => setShowNewModal(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Scenario
        </Button>
      </div>

      {showNewModal && (
        <NewScenarioModal
          onClose={() => setShowNewModal(false)}
          onCreated={(scenario) => {
            setScenarios((prev) => [scenario, ...prev]);
            setShowNewModal(false);
          }}
        />
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pipeline Value</p>
                <p className="text-2xl font-bold">
                  {formatCurrency(totalPipelineValue)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  Active Scenarios
                </p>
                <p className="text-2xl font-bold">{scenarios.length}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  Recommended Scenarios
                </p>
                <p className="text-2xl font-bold">{recommendedScenarios.length}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Margin %</p>
                <p className="text-2xl font-bold">{avgMargin.toFixed(1)}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:border-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">
            Loading pricing data...
          </span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <Button variant="outline" onClick={fetchData}>
            Retry
          </Button>
        </div>
      ) : (
        <>
          {/* Scenarios Tab */}
          {activeTab === "scenarios" && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">
                      Pricing Scenarios
                      <span className="ml-2 text-sm font-normal text-muted-foreground">
                        ({scenarios.length} results)
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {scenarios.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-12">
                        <p className="text-muted-foreground">
                          No pricing scenarios found.
                        </p>
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b text-left">
                              <th className="pb-3 pr-4 font-medium text-muted-foreground">
                                Name
                              </th>
                              <th className="pb-3 pr-4 font-medium text-muted-foreground">
                                Type
                              </th>
                              <th className="pb-3 pr-4 font-medium text-muted-foreground">
                                Total Price
                              </th>
                              <th className="pb-3 pr-4 font-medium text-muted-foreground">
                                Margin %
                              </th>
                              <th className="pb-3 pr-4 font-medium text-muted-foreground">
                                Status
                              </th>
                              <th className="pb-3 pr-4 font-medium text-muted-foreground">
                                Approval
                              </th>
                              <th className="pb-3 font-medium text-muted-foreground">
                                Date
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {scenarios.map((scenario) => {
                              const approvalStatus = getApprovalStatus(
                                scenario.id
                              );
                              return (
                                <tr
                                  key={scenario.id}
                                  onClick={() =>
                                    handleScenarioClick(scenario)
                                  }
                                  className={`border-b cursor-pointer transition-colors hover:bg-muted/50 ${
                                    selectedScenario?.id === scenario.id
                                      ? "bg-muted/50"
                                      : ""
                                  }`}
                                >
                                  <td className="py-3 pr-4 font-medium">
                                    {scenario.name || "--"}
                                  </td>
                                  <td className="py-3 pr-4 text-muted-foreground">
                                    {STRATEGY_TYPE_LABELS[
                                      scenario.strategy_type
                                    ] || scenario.strategy_type || "--"}
                                  </td>
                                  <td className="py-3 pr-4 font-medium">
                                    {formatCurrency(scenario.total_price)}
                                  </td>
                                  <td className="py-3 pr-4">
                                    {scenario.margin_pct != null
                                      ? `${Number(scenario.margin_pct).toFixed(1)}%`
                                      : "--"}
                                  </td>
                                  <td className="py-3 pr-4">
                                    {scenario.is_recommended ? (
                                      <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-700">
                                        Recommended
                                      </span>
                                    ) : (
                                      <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-700">
                                        Draft
                                      </span>
                                    )}
                                  </td>
                                  <td className="py-3 pr-4">
                                    {approvalStatus ? (
                                      <span
                                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                          approvalStatus === "approved"
                                            ? "bg-green-100 text-green-700"
                                            : approvalStatus === "rejected"
                                              ? "bg-red-100 text-red-700"
                                              : "bg-yellow-100 text-yellow-700"
                                        }`}
                                      >
                                        {approvalStatus
                                          .charAt(0)
                                          .toUpperCase() +
                                          approvalStatus.slice(1)}
                                      </span>
                                    ) : (
                                      <span className="text-xs text-muted-foreground">
                                        --
                                      </span>
                                    )}
                                  </td>
                                  <td className="py-3 text-muted-foreground text-xs">
                                    {formatDate(scenario.created_at)}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Scenario Detail Panel */}
              <div className="lg:col-span-1">
                {selectedScenario ? (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">
                        {selectedScenario.name}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Pricing Summary */}
                      <div>
                        <h4 className="text-sm font-semibold mb-2">
                          Pricing Summary
                        </h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Strategy
                            </span>
                            <span className="font-medium">
                              {selectedScenario.strategy_type_display || STRATEGY_TYPE_LABELS[selectedScenario.strategy_type] || selectedScenario.strategy_type}
                            </span>
                          </div>
                          <div className="flex justify-between border-t pt-2">
                            <span className="font-semibold">Total Price</span>
                            <span className="font-bold text-primary">
                              {formatCurrency(selectedScenario.total_price)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Profit
                            </span>
                            <span className="font-medium">
                              {formatCurrency(selectedScenario.profit)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Margin
                            </span>
                            <span className="font-medium">
                              {selectedScenario.margin_pct != null
                                ? `${Number(selectedScenario.margin_pct).toFixed(1)}%`
                                : "--"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              P(Win)
                            </span>
                            <span className="font-medium">
                              {selectedScenario.probability_of_win != null
                                ? `${(Number(selectedScenario.probability_of_win) * 100).toFixed(0)}%`
                                : "--"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Expected Value
                            </span>
                            <span className="font-medium">
                              {formatCurrency(selectedScenario.expected_value)}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* LOE Breakdown */}
                      <div>
                        <h4 className="text-sm font-semibold mb-2">
                          LOE Breakdown
                        </h4>
                        {loadingLOEs ? (
                          <div className="flex items-center justify-center py-4">
                            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                          </div>
                        ) : scenarioLOEs.length === 0 ? (
                          <p className="text-xs text-muted-foreground">
                            No LOE estimates linked to this deal.
                          </p>
                        ) : (
                          <div className="space-y-2">
                            <div className="grid grid-cols-3 text-xs text-muted-foreground font-medium border-b pb-1">
                              <span>Task / Category</span>
                              <span className="text-right">WBS</span>
                              <span className="text-right">Est. Hours</span>
                            </div>
                            {scenarioLOEs.flatMap((loe) =>
                              (loe.wbs_elements || []).map((wbs, idx) => (
                                <div
                                  key={`${loe.id}-${idx}`}
                                  className="grid grid-cols-3 text-xs"
                                >
                                  <span className="text-muted-foreground truncate">
                                    {wbs.name}
                                    <span className="ml-1 text-[10px] opacity-60">({wbs.labor_category})</span>
                                  </span>
                                  <span className="text-right font-mono">{wbs.wbs_id}</span>
                                  <span className="text-right font-medium">
                                    {wbs.hours_estimated?.toLocaleString() || "--"}
                                  </span>
                                </div>
                              ))
                            )}
                            <div className="grid grid-cols-3 text-xs font-semibold border-t pt-1">
                              <span>Total</span>
                              <span></span>
                              <span className="text-right">
                                {scenarioLOEs
                                  .reduce(
                                    (sum, l) => sum + (l.total_hours || 0),
                                    0
                                  )
                                  .toLocaleString()}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ) : (
                  <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                      <BarChart3 className="h-10 w-10 text-muted-foreground mb-3" />
                      <p className="text-sm text-muted-foreground text-center">
                        Select a scenario to view cost breakdown and LOE
                        estimates
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          )}

          {/* Rate Cards Tab */}
          {activeTab === "rate-cards" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  Rate Cards
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    ({rateCards.length} labor categories)
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {rateCards.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12">
                    <p className="text-muted-foreground">
                      No rate cards found.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b text-left">
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">Labor Category</th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">GSA Equivalent</th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">Internal Rate</th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">GSA Rate</th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">Proposed Rate</th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">Market Range</th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">Exp (yrs)</th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">Clearance</th>
                          <th className="pb-3 font-medium text-muted-foreground">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rateCards.map((card) => (
                          <tr key={card.id} className="border-b transition-colors hover:bg-muted/50">
                            <td className="py-3 pr-4 font-medium">{card.labor_category}</td>
                            <td className="py-3 pr-4 text-muted-foreground">{card.gsa_equivalent || "--"}</td>
                            <td className="py-3 pr-4">${toNum(card.internal_rate).toFixed(2)}/hr</td>
                            <td className="py-3 pr-4 text-muted-foreground">
                              {card.gsa_rate ? `$${toNum(card.gsa_rate).toFixed(2)}/hr` : "--"}
                            </td>
                            <td className="py-3 pr-4 font-medium">${toNum(card.proposed_rate).toFixed(2)}/hr</td>
                            <td className="py-3 pr-4 text-xs text-muted-foreground">
                              {card.market_low && card.market_high
                                ? `$${toNum(card.market_low).toFixed(0)} – $${toNum(card.market_high).toFixed(0)}`
                                : "--"}
                            </td>
                            <td className="py-3 pr-4 text-muted-foreground">{card.experience_years || "--"}</td>
                            <td className="py-3 pr-4">
                              {card.clearance_required ? (
                                <span className="inline-flex items-center rounded-full bg-amber-100 text-amber-700 px-2 py-0.5 text-xs font-medium">Required</span>
                              ) : (
                                <span className="text-xs text-muted-foreground">None</span>
                              )}
                            </td>
                            <td className="py-3">
                              <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                                card.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                              }`}>
                                {card.is_active ? "Active" : "Inactive"}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* LOE Estimates Tab */}
          {activeTab === "loe-estimates" && (
            <div className="space-y-4">
              {loeEstimates.length === 0 ? (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <p className="text-muted-foreground">
                      No LOE estimates found.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                loeEstimates.map((loe) => (
                  <Card key={loe.id}>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center justify-between">
                        <span>
                          LOE Estimate v{loe.version}
                          <span className="ml-2 text-sm font-normal text-muted-foreground">
                            {loe.estimation_method_display || loe.estimation_method}
                          </span>
                        </span>
                        <div className="flex items-center gap-4 text-sm font-normal text-muted-foreground">
                          <span>{loe.total_hours?.toLocaleString() || 0} total hrs</span>
                          <span>{loe.total_ftes?.toFixed(1) || 0} FTEs</span>
                          <span>{loe.duration_months || 0} months</span>
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                            loe.confidence_level >= 0.7 ? "bg-green-100 text-green-700" :
                            loe.confidence_level >= 0.5 ? "bg-amber-100 text-amber-700" :
                            "bg-red-100 text-red-700"
                          }`}>
                            {(loe.confidence_level * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {loe.wbs_elements && loe.wbs_elements.length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b text-left">
                                <th className="pb-3 pr-4 font-medium text-muted-foreground">WBS ID</th>
                                <th className="pb-3 pr-4 font-medium text-muted-foreground">Task</th>
                                <th className="pb-3 pr-4 font-medium text-muted-foreground">Labor Category</th>
                                <th className="pb-3 pr-4 font-medium text-muted-foreground">Optimistic</th>
                                <th className="pb-3 pr-4 font-medium text-muted-foreground">Likely</th>
                                <th className="pb-3 pr-4 font-medium text-muted-foreground">Pessimistic</th>
                                <th className="pb-3 font-medium text-muted-foreground">Estimated Hrs</th>
                              </tr>
                            </thead>
                            <tbody>
                              {loe.wbs_elements.map((wbs, idx) => (
                                <tr key={idx} className="border-b transition-colors hover:bg-muted/50">
                                  <td className="py-3 pr-4 font-mono text-xs">{wbs.wbs_id}</td>
                                  <td className="py-3 pr-4 font-medium">{wbs.name}</td>
                                  <td className="py-3 pr-4 text-muted-foreground">{wbs.labor_category}</td>
                                  <td className="py-3 pr-4 text-muted-foreground">{wbs.hours_optimistic?.toLocaleString() || "--"}</td>
                                  <td className="py-3 pr-4 text-muted-foreground">{wbs.hours_likely?.toLocaleString() || "--"}</td>
                                  <td className="py-3 pr-4 text-muted-foreground">{wbs.hours_pessimistic?.toLocaleString() || "--"}</td>
                                  <td className="py-3 font-medium">{wbs.hours_estimated?.toLocaleString() || "--"}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="text-sm text-muted-foreground text-center py-4">
                          No WBS elements in this estimate.
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
