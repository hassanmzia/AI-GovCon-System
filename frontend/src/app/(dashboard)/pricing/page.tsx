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
  ChevronDown,
  ChevronRight,
  DollarSign,
  TrendingUp,
  CheckCircle,
  BarChart3,
  X,
} from "lucide-react";

type ActiveTab = "scenarios" | "rate-cards" | "loe-estimates";

const SCENARIO_TYPE_LABELS: Record<string, string> = {
  cost_plus: "Cost Plus",
  fixed_price: "Fixed Price",
  time_material: "T&M",
  idiq: "IDIQ",
};

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  under_review: "bg-yellow-100 text-yellow-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "Draft",
  under_review: "Under Review",
  approved: "Approved",
  rejected: "Rejected",
};

function formatCurrency(value: number | null | undefined): string {
  if (value == null) return "--";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
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
  const [scenarioType, setScenarioType] = useState("fixed_price");
  const [dealId, setDealId] = useState("");
  const [deals, setDeals] = useState<Deal[]>([]);
  const [dealsLoading, setDealsLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scenarioTypes = [
    { value: "cost_plus", label: "Cost Plus" },
    { value: "fixed_price", label: "Fixed Price" },
    { value: "time_material", label: "Time & Materials" },
    { value: "idiq", label: "IDIQ" },
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
      const scenario = await createScenario({ name: name.trim(), scenario_type: scenarioType as PricingScenario["scenario_type"], deal: dealId });
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
            <label className="text-sm font-medium">Type</label>
            <select value={scenarioType} onChange={(e) => setScenarioType(e.target.value)} className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
              {scenarioTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
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
  const [expandedRateCards, setExpandedRateCards] = useState<Set<string>>(
    new Set()
  );
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
      const data = await getLOEEstimates({ scenario: scenario.id });
      setScenarioLOEs(data.results || []);
    } catch (err) {
      console.error("Error fetching scenario LOEs:", err);
      setScenarioLOEs([]);
    } finally {
      setLoadingLOEs(false);
    }
  };

  const toggleRateCardExpand = (id: string) => {
    setExpandedRateCards((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Computed summary stats
  const approvedScenarios = scenarios.filter((s) => s.status === "approved");
  const totalPipelineValue = scenarios.reduce(
    (sum, s) => sum + (s.total_price || 0),
    0
  );
  const avgMargin =
    scenarios.length > 0
      ? scenarios.reduce((sum, s) => sum + (s.margin_percentage || 0), 0) /
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
                  Approved Scenarios
                </p>
                <p className="text-2xl font-bold">{approvedScenarios.length}</p>
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
                                    {SCENARIO_TYPE_LABELS[
                                      scenario.scenario_type
                                    ] || scenario.scenario_type || "--"}
                                  </td>
                                  <td className="py-3 pr-4 font-medium">
                                    {formatCurrency(scenario.total_price)}
                                  </td>
                                  <td className="py-3 pr-4">
                                    {scenario.margin_percentage != null
                                      ? `${Number(scenario.margin_percentage).toFixed(1)}%`
                                      : "--"}
                                  </td>
                                  <td className="py-3 pr-4">
                                    <span
                                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                        STATUS_COLORS[scenario.status] ||
                                        "bg-gray-100 text-gray-700"
                                      }`}
                                    >
                                      {STATUS_LABELS[scenario.status] ||
                                        scenario.status}
                                    </span>
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
                      {/* Cost Summary */}
                      <div>
                        <h4 className="text-sm font-semibold mb-2">
                          Cost Summary
                        </h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Direct Cost
                            </span>
                            <span className="font-medium">
                              {formatCurrency(
                                selectedScenario.total_direct_cost
                              )}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Indirect Cost
                            </span>
                            <span className="font-medium">
                              {formatCurrency(
                                selectedScenario.total_indirect_cost
                              )}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Fee</span>
                            <span className="font-medium">
                              {formatCurrency(selectedScenario.total_fee)}
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
                              Margin
                            </span>
                            <span className="font-medium">
                              {selectedScenario.margin_percentage != null
                                ? `${Number(selectedScenario.margin_percentage).toFixed(1)}%`
                                : "--"}
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
                            No LOE estimates for this scenario.
                          </p>
                        ) : (
                          <div className="space-y-2">
                            <div className="grid grid-cols-3 text-xs text-muted-foreground font-medium border-b pb-1">
                              <span>Category</span>
                              <span className="text-right">Hours</span>
                              <span className="text-right">Cost</span>
                            </div>
                            {scenarioLOEs.map((loe) => (
                              <div
                                key={loe.id}
                                className="grid grid-cols-3 text-xs"
                              >
                                <span className="text-muted-foreground truncate">
                                  {loe.labor_category}
                                  {loe.level ? ` (${loe.level})` : ""}
                                </span>
                                <span className="text-right">
                                  {loe.total_hours?.toLocaleString() || "--"}
                                </span>
                                <span className="text-right font-medium">
                                  {formatCurrency(loe.total_cost)}
                                </span>
                              </div>
                            ))}
                            <div className="grid grid-cols-3 text-xs font-semibold border-t pt-1">
                              <span>Total</span>
                              <span className="text-right">
                                {scenarioLOEs
                                  .reduce(
                                    (sum, l) => sum + (l.total_hours || 0),
                                    0
                                  )
                                  .toLocaleString()}
                              </span>
                              <span className="text-right">
                                {formatCurrency(
                                  scenarioLOEs.reduce(
                                    (sum, l) => sum + (l.total_cost || 0),
                                    0
                                  )
                                )}
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
                    ({rateCards.length} results)
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
                  <div className="space-y-2">
                    {rateCards.map((card) => {
                      const isExpanded = expandedRateCards.has(card.id);
                      return (
                        <div
                          key={card.id}
                          className="border rounded-lg overflow-hidden"
                        >
                          <button
                            onClick={() => toggleRateCardExpand(card.id)}
                            className="w-full flex items-center justify-between px-4 py-3 hover:bg-muted/50 transition-colors text-left"
                          >
                            <div className="flex items-center gap-4">
                              {isExpanded ? (
                                <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                              ) : (
                                <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                              )}
                              <div>
                                <span className="font-medium text-sm">
                                  {card.name}
                                </span>
                                <span className="ml-3 text-xs text-muted-foreground">
                                  FY {card.fiscal_year}
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <span
                                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                                  card.is_active
                                    ? "bg-green-100 text-green-700"
                                    : "bg-gray-100 text-gray-500"
                                }`}
                              >
                                {card.is_active ? "Active" : "Inactive"}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {card.rates?.length || 0} rates
                              </span>
                            </div>
                          </button>

                          {isExpanded && card.rates && card.rates.length > 0 && (
                            <div className="border-t bg-muted/20 px-4 py-3">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="border-b text-left">
                                    <th className="pb-2 pr-4 font-medium text-muted-foreground">
                                      Labor Category
                                    </th>
                                    <th className="pb-2 pr-4 font-medium text-muted-foreground">
                                      Level
                                    </th>
                                    <th className="pb-2 pr-4 font-medium text-muted-foreground">
                                      Hourly Rate
                                    </th>
                                    <th className="pb-2 pr-4 font-medium text-muted-foreground">
                                      Indirect Rate
                                    </th>
                                    <th className="pb-2 font-medium text-muted-foreground">
                                      Escalation
                                    </th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {card.rates.map((rate, idx) => (
                                    <tr
                                      key={idx}
                                      className="border-b last:border-0"
                                    >
                                      <td className="py-2 pr-4 font-medium">
                                        {rate.labor_category || "--"}
                                      </td>
                                      <td className="py-2 pr-4 text-muted-foreground">
                                        {rate.level || "--"}
                                      </td>
                                      <td className="py-2 pr-4">
                                        $
                                        {Number(rate.hourly_rate).toFixed(2)}
                                        /hr
                                      </td>
                                      <td className="py-2 pr-4 text-muted-foreground">
                                        {rate.indirect_rate != null
                                          ? `${(Number(rate.indirect_rate) * 100).toFixed(1)}%`
                                          : "--"}
                                      </td>
                                      <td className="py-2 text-muted-foreground">
                                        {rate.escalation_rate != null
                                          ? `${(Number(rate.escalation_rate) * 100).toFixed(1)}%`
                                          : "--"}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          )}

                          {isExpanded &&
                            (!card.rates || card.rates.length === 0) && (
                              <div className="border-t bg-muted/20 px-4 py-4">
                                <p className="text-xs text-muted-foreground text-center">
                                  No rates defined for this rate card.
                                </p>
                              </div>
                            )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* LOE Estimates Tab */}
          {activeTab === "loe-estimates" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  LOE Estimates
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    ({loeEstimates.length} results)
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loeEstimates.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12">
                    <p className="text-muted-foreground">
                      No LOE estimates found.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b text-left">
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">
                            Labor Category
                          </th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">
                            Level
                          </th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">
                            Hrs/Month
                          </th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">
                            Months
                          </th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">
                            Total Hours
                          </th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">
                            Hourly Rate
                          </th>
                          <th className="pb-3 font-medium text-muted-foreground">
                            Total Cost
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {loeEstimates.map((loe) => (
                          <tr
                            key={loe.id}
                            className="border-b transition-colors hover:bg-muted/50"
                          >
                            <td className="py-3 pr-4 font-medium">
                              {loe.labor_category || "--"}
                            </td>
                            <td className="py-3 pr-4 text-muted-foreground">
                              {loe.level || "--"}
                            </td>
                            <td className="py-3 pr-4 text-muted-foreground">
                              {loe.hours_per_month?.toLocaleString() || "--"}
                            </td>
                            <td className="py-3 pr-4 text-muted-foreground">
                              {loe.months || "--"}
                            </td>
                            <td className="py-3 pr-4 font-medium">
                              {loe.total_hours?.toLocaleString() || "--"}
                            </td>
                            <td className="py-3 pr-4 text-muted-foreground">
                              {loe.hourly_rate != null
                                ? `$${Number(loe.hourly_rate).toFixed(2)}/hr`
                                : "--"}
                            </td>
                            <td className="py-3 font-medium">
                              {formatCurrency(loe.total_cost)}
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
        </>
      )}
    </div>
  );
}
