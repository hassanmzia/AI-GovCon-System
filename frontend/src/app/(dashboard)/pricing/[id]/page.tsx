"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getScenario, getLOEEstimates, getCostModels } from "@/services/pricing";
import { PricingScenario, LOEEstimate, CostModel } from "@/types/pricing";
import {
  Loader2,
  ArrowLeft,
  DollarSign,
  TrendingUp,
  BarChart3,
  Users,
  CheckCircle,
  Clock,
  AlertTriangle,
  Target,
  Layers,
} from "lucide-react";

function formatCurrency(value: number | null | undefined): string {
  if (value == null) return "--";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPct(value: number | null | undefined): string {
  if (value == null) return "--";
  return `${value.toFixed(1)}%`;
}

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

const SCENARIO_TYPE_LABELS: Record<string, string> = {
  cost_plus: "Cost Plus",
  fixed_price: "Fixed Price",
  time_material: "Time & Materials",
  idiq: "IDIQ",
};

// ── Win Probability Curve ────────────────────────────────────────────────────
function WinProbabilityCurve({ scenario }: { scenario: PricingScenario }) {
  const margin = scenario.margin_percentage || 0;
  // Simulated win probability curve based on margin
  const points = [0, 5, 10, 15, 20, 25, 30, 35, 40].map((m) => ({
    margin: m,
    pWin: Math.max(5, Math.min(95, 90 - m * 2.2)),
  }));

  const currentPWin = Math.max(5, Math.min(95, 90 - margin * 2.2));
  const svgWidth = 380;
  const svgHeight = 140;
  const padL = 40;
  const padB = 30;
  const padT = 10;
  const padR = 10;
  const w = svgWidth - padL - padR;
  const h = svgHeight - padB - padT;

  const xScale = (m: number) => padL + (m / 40) * w;
  const yScale = (p: number) => padT + h - (p / 100) * h;

  const pathD = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${xScale(p.margin)} ${yScale(p.pWin)}`)
    .join(" ");

  const curX = xScale(margin);
  const curY = yScale(currentPWin);

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-sm">Win Probability Curve</h3>
        <span className="text-2xl font-bold text-green-600">{currentPWin.toFixed(0)}%</span>
      </div>
      <svg width={svgWidth} height={svgHeight} className="w-full">
        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map((p) => (
          <g key={p}>
            <line
              x1={padL}
              y1={yScale(p)}
              x2={padL + w}
              y2={yScale(p)}
              stroke="#e5e7eb"
              strokeWidth={1}
            />
            <text x={padL - 5} y={yScale(p) + 4} textAnchor="end" fontSize={9} fill="#9ca3af">
              {p}%
            </text>
          </g>
        ))}
        {/* Margin labels */}
        {[0, 10, 20, 30, 40].map((m) => (
          <text
            key={m}
            x={xScale(m)}
            y={svgHeight - 5}
            textAnchor="middle"
            fontSize={9}
            fill="#9ca3af"
          >
            {m}%
          </text>
        ))}
        {/* Axis labels */}
        <text x={padL + w / 2} y={svgHeight} textAnchor="middle" fontSize={9} fill="#6b7280">
          Margin %
        </text>
        {/* Curve */}
        <path d={pathD} fill="none" stroke="#3b82f6" strokeWidth={2.5} />
        {/* Current position */}
        <line x1={curX} y1={padT} x2={curX} y2={padT + h} stroke="#ef4444" strokeWidth={1} strokeDasharray="4 2" />
        <circle cx={curX} cy={curY} r={5} fill="#ef4444" />
        <text x={curX + 8} y={curY - 6} fontSize={10} fill="#ef4444" fontWeight="bold">
          {margin.toFixed(1)}%
        </text>
      </svg>
      <p className="text-xs text-muted-foreground mt-1 text-center">
        Lower margins increase win probability — optimize by adjusting cost structure
      </p>
    </div>
  );
}

// ── Sensitivity Chart ────────────────────────────────────────────────────────
function SensitivityChart({ costModel }: { costModel: CostModel | null }) {
  if (!costModel) {
    return (
      <div className="flex items-center justify-center h-32 text-muted-foreground text-sm">
        No cost model available
      </div>
    );
  }

  const total = Number(costModel.total_cost) || 1;
  const items = [
    { label: "Direct Labor", value: Number(costModel.direct_labor), color: "bg-blue-500" },
    { label: "Fringe", value: Number(costModel.fringe_benefits), color: "bg-indigo-400" },
    { label: "Overhead", value: Number(costModel.overhead), color: "bg-violet-400" },
    { label: "G&A", value: Number(costModel.ga_expense), color: "bg-purple-400" },
    { label: "ODCs", value: Number(costModel.odcs), color: "bg-cyan-500" },
    { label: "Subcontractors", value: Number(costModel.subcontractor_costs), color: "bg-teal-500" },
    { label: "Travel", value: Number(costModel.travel), color: "bg-orange-400" },
    { label: "Materials", value: Number(costModel.materials), color: "bg-amber-400" },
  ].filter((i) => i.value > 0).sort((a, b) => b.value - a.value);

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-2">
          <span className="text-xs w-28 text-muted-foreground">{item.label}</span>
          <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full ${item.color} rounded-full`}
              style={{ width: `${(item.value / total) * 100}%` }}
            />
          </div>
          <span className="text-xs w-20 text-right font-medium">
            {formatCurrency(item.value)}
          </span>
          <span className="text-xs w-12 text-right text-muted-foreground">
            {((item.value / total) * 100).toFixed(1)}%
          </span>
        </div>
      ))}
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────
export default function PricingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [scenario, setScenario] = useState<PricingScenario | null>(null);
  const [loeEstimates, setLoeEstimates] = useState<LOEEstimate[]>([]);
  const [costModel, setCostModel] = useState<CostModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await getScenario(id);
      setScenario(s);

      const [loeRes, cmRes] = await Promise.all([
        getLOEEstimates({ scenario: id }),
        getCostModels({ deal: s.deal }),
      ]);
      setLoeEstimates(loeRes.results);
      if (cmRes.results.length > 0) setCostModel(cmRes.results[0]);
    } catch {
      setError("Failed to load pricing scenario.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !scenario) {
    return (
      <div className="p-6">
        <p className="text-red-600">{error || "Scenario not found."}</p>
        <Button variant="outline" onClick={() => router.back()} className="mt-4">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back
        </Button>
      </div>
    );
  }

  const totalHours = loeEstimates.reduce((s, e) => s + e.total_hours, 0);
  const feeAmt = Number(scenario.total_fee) || 0;
  const directCost = Number(scenario.total_direct_cost) || 0;
  const indirectCost = Number(scenario.total_indirect_cost) || 0;
  const totalPrice = Number(scenario.total_price) || 0;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/pricing">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" /> Pricing
          </Button>
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{scenario.name}</h1>
            <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${STATUS_COLORS[scenario.status]}`}>
              {STATUS_LABELS[scenario.status]}
            </span>
            <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700 font-medium">
              {SCENARIO_TYPE_LABELS[scenario.scenario_type]}
            </span>
          </div>
          {scenario.deal_name && (
            <p className="text-muted-foreground mt-0.5">Deal: {scenario.deal_name}</p>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <DollarSign className="h-4 w-4" />
              <span className="text-xs">Total Price</span>
            </div>
            <div className="text-2xl font-bold">{formatCurrency(totalPrice)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <TrendingUp className="h-4 w-4" />
              <span className="text-xs">Margin</span>
            </div>
            <div className="text-2xl font-bold">{formatPct(scenario.margin_percentage)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Layers className="h-4 w-4" />
              <span className="text-xs">Fee</span>
            </div>
            <div className="text-2xl font-bold">{formatCurrency(feeAmt)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Users className="h-4 w-4" />
              <span className="text-xs">Total Hours</span>
            </div>
            <div className="text-2xl font-bold">{totalHours.toLocaleString()}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Win Probability Curve */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="h-4 w-4" /> Price-to-Win Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <WinProbabilityCurve scenario={scenario} />
          </CardContent>
        </Card>

        {/* Cost Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4" /> Cost Structure Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <SensitivityChart costModel={costModel} />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <DollarSign className="h-4 w-4" /> Cost Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between py-1.5 border-b">
                <span className="text-sm text-muted-foreground">Direct Costs</span>
                <span className="font-semibold">{formatCurrency(directCost)}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b">
                <span className="text-sm text-muted-foreground">Indirect Costs</span>
                <span className="font-semibold">{formatCurrency(indirectCost)}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b">
                <span className="text-sm text-muted-foreground">Fee</span>
                <span className="font-semibold">{formatCurrency(feeAmt)}</span>
              </div>
              <div className="flex justify-between py-1.5 font-bold text-lg">
                <span>Total Price</span>
                <span className="text-blue-700">{formatCurrency(totalPrice)}</span>
              </div>
              {costModel && (
                <div className="pt-2 space-y-1.5 text-xs text-muted-foreground">
                  <div className="flex justify-between">
                    <span>Fringe Rate</span>
                    <span>{formatPct(costModel.fringe_rate)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Overhead Rate</span>
                    <span>{formatPct(costModel.overhead_rate)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>G&A Rate</span>
                    <span>{formatPct(costModel.ga_rate)}</span>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* LOE Estimates */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Users className="h-4 w-4" /> Labor Category Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loeEstimates.length === 0 ? (
              <div className="flex items-center justify-center h-24 text-muted-foreground text-sm">
                No LOE estimates linked to this scenario
              </div>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-4 gap-1 text-xs text-muted-foreground pb-1 border-b">
                  <span>Category</span>
                  <span className="text-right">Hours/Mo</span>
                  <span className="text-right">Months</span>
                  <span className="text-right">Total Cost</span>
                </div>
                {loeEstimates.map((e) => (
                  <div key={e.id} className="grid grid-cols-4 gap-1 text-sm py-1 border-b last:border-0">
                    <span className="truncate">{e.labor_category}</span>
                    <span className="text-right">{e.hours_per_month}</span>
                    <span className="text-right">{e.months}</span>
                    <span className="text-right font-medium">{formatCurrency(e.total_cost)}</span>
                  </div>
                ))}
                <div className="grid grid-cols-4 gap-1 text-sm pt-2 font-bold">
                  <span>Total</span>
                  <span></span>
                  <span></span>
                  <span className="text-right text-blue-700">
                    {formatCurrency(loeEstimates.reduce((s, e) => s + e.total_cost, 0))}
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Approval Status */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            {scenario.is_approved ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : scenario.status === "under_review" ? (
              <Clock className="h-4 w-4 text-yellow-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-gray-400" />
            )}
            Approval Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <span className={`px-3 py-1.5 rounded-full text-sm font-medium ${STATUS_COLORS[scenario.status]}`}>
              {STATUS_LABELS[scenario.status]}
            </span>
            {scenario.is_approved && (
              <span className="text-green-600 text-sm font-medium flex items-center gap-1">
                <CheckCircle className="h-4 w-4" /> Approved for submission
              </span>
            )}
            {!scenario.is_approved && scenario.status === "draft" && (
              <span className="text-muted-foreground text-sm">
                Submit for review when ready
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
