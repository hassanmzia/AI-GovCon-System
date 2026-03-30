"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import api, { orchestratorApi } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { AgentScorecard } from "@/components/ai-metrics/agent-scorecard";
import { ForecastChart } from "@/components/dashboard/forecast-chart";
import { RiskScoreDisplay } from "@/components/governance/risk-score-display";
import {
  Brain,
  Loader2,
  AlertTriangle,
  TrendingUp,
  Clock,
  Users,
  Target,
  CheckCircle,
  AlertCircle,
  MinusCircle,
  RefreshCw,
  BarChart2,
  Cpu,
  GitBranch,
  Copy,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";

// --- Types ---
interface AgentRun {
  agent_name: string;
  status: string;
  latency_ms: number | null;
  cost_usd: number | null;
  success: boolean | null;
  confidence: number | null;
  hallucination_flags: number;
  override: boolean;
  risk_score: number | null;
  created_at?: string;
  days?: number;
}

interface WinLossRecord {
  id: string;
  won: boolean;
  ai_confidence: number | null;
  deal_stage: string;
  total_value?: number;
}

interface EnforcementEntry {
  id: string;
  decision: "allowed" | "blocked" | "hitl_required";
  timestamp: string;
}

interface ForecastQuarter {
  quarter: string;
  pipeline_value: number;
  weighted_value: number;
  deal_count: number;
  low?: number;
  high?: number;
}

interface GraphMeta {
  id: string;
  title: string;
  description: string;
  type: string;
}

// --- Mermaid Renderer for Graph Visualization ---
function InlineMermaidRenderer({ code, id }: { code: string; id: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!code) return;
    let cancelled = false;

    (async () => {
      try {
        const mermaidModule = await import("mermaid");
        const mermaid = mermaidModule.default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "default",
          securityLevel: "loose",
          fontFamily: "ui-sans-serif, system-ui, sans-serif",
          flowchart: { curve: "basis", padding: 15 },
        });
        const stale = document.getElementById(`gmermaid-${id}`);
        if (stale) stale.remove();
        const result = await mermaid.render(`gmermaid-${id}`, code);
        if (!cancelled) {
          setSvg(result.svg);
          setError(false);
        }
      } catch {
        if (!cancelled) setError(true);
      }
    })();

    return () => { cancelled = true; };
  }, [code, id]);

  if (error) {
    return (
      <pre className="overflow-x-auto rounded-lg bg-muted p-4 text-xs leading-relaxed text-foreground/80 border border-border">
        <code>{code}</code>
      </pre>
    );
  }

  if (!svg) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin mr-2" /> Rendering graph...
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="rounded-lg border bg-background p-4 overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}

// --- Constants ---
const KNOWN_AGENTS = [
  "scout_agent",               // 01 · Opportunity Scout
  "fit_agent",                 // 02 · PWin Analyst
  "competitor_sim_agent",      // 03 · Competitive Intel
  "compliance_agent",          // 04 · Compliance Checker
  "teaming_agent",             // 05 · Teaming Advisor
  "rfp_analyst_agent",         // 06 · RFP Parser
  "marketing_agent",           // 07 · Win Theme Generator
  "proposal_writer_agent",     // 08 · Technical Approach Drafter
  "past_performance_agent",    // 09 · Past Performance Mapper
  "management_approach_agent", // 10 · Management Approach Drafter
  "pricing_agent",             // 11 · Price-to-Win Analyst
  "solution_architect_agent",  // 12 · Cost Volume Builder
  "red_team_agent",            // 13 · Discriminator Reviewer
  "security_compliance_agent", // 14 · Section 508 Checker
  "cui_handler_agent",         // 15 · CUI Handler
  "submission_agent",          // 16 · Submission Packager
  "learning_agent",            // 17 · Award Tracker
  "deal_pipeline_agent",       // 18 · Pipeline Orchestrator
  "synthetic_evaluator_agent", // 19 · Synthetic Evaluator
];

// --- Helpers ---
function formatPct(v: number | null): string {
  if (v === null) return "—";
  return `${v.toFixed(1)}%`;
}

function formatDays(v: number | null): string {
  if (v === null) return "—";
  return `${v.toFixed(1)}d`;
}

function stageColor(stage: string): string {
  const map: Record<string, string> = {
    qualification: "#3b82f6",
    proposal: "#8b5cf6",
    review: "#f59e0b",
    submitted: "#10b981",
    awarded: "#16a34a",
    lost: "#ef4444",
  };
  return map[stage?.toLowerCase()] ?? "#6b7280";
}

// --- KPI Card ---
function KpiCard({
  title,
  value,
  subtitle,
  icon,
  colorClass,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  colorClass: string;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              {title}
            </p>
            <p className={`text-3xl font-bold ${colorClass}`}>{value}</p>
            {subtitle && (
              <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
            )}
          </div>
          <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}

// --- Main Page ---
export default function AICommandCenterPage() {
  // Agent runs
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);
  const [agentRunsLoading, setAgentRunsLoading] = useState(true);
  const [agentRunsError, setAgentRunsError] = useState<string | null>(null);

  // Win/loss
  const [winLoss, setWinLoss] = useState<WinLossRecord[]>([]);
  const [winLossLoading, setWinLossLoading] = useState(true);
  const [winLossError, setWinLossError] = useState<string | null>(null);

  // Enforcement log
  const [enforcement, setEnforcement] = useState<EnforcementEntry[]>([]);
  const [enforcementLoading, setEnforcementLoading] = useState(true);
  const [enforcementError, setEnforcementError] = useState<string | null>(null);

  // Recent 7-day agent runs (for hallucination monitor)
  const [recentRuns, setRecentRuns] = useState<AgentRun[]>([]);

  // Forecast quarters (stub from pipeline)
  const [forecastQuarters, setForecastQuarters] = useState<ForecastQuarter[]>([]);

  // Risk score for display stub
  const [riskScore] = useState(null);

  // Graph visualization
  const [graphs, setGraphs] = useState<GraphMeta[]>([]);
  const [selectedGraph, setSelectedGraph] = useState<string | null>(null);
  const [graphMermaid, setGraphMermaid] = useState<string>("");
  const [graphTitle, setGraphTitle] = useState<string>("");
  const [graphLoading, setGraphLoading] = useState(false);
  const [showGraphSource, setShowGraphSource] = useState(false);

  const fetchAgentRuns = useCallback(async () => {
    setAgentRunsLoading(true);
    setAgentRunsError(null);
    try {
      const res = await api.get("/analytics/agent-runs/?limit=100");
      const data = res.data;
      const runs: AgentRun[] = Array.isArray(data)
        ? data
        : data.results ?? [];
      setAgentRuns(runs);
    } catch (e) {
      setAgentRunsError(
        e instanceof Error ? e.message : "Failed to load agent runs"
      );
    } finally {
      setAgentRunsLoading(false);
    }
  }, []);

  const fetchWinLoss = useCallback(async () => {
    setWinLossLoading(true);
    setWinLossError(null);
    try {
      const res = await api.get("/analytics/win-loss/?limit=50");
      const data = res.data;
      setWinLoss(Array.isArray(data) ? data : data.results ?? []);
    } catch (e) {
      setWinLossError(
        e instanceof Error ? e.message : "Failed to load win/loss data"
      );
    } finally {
      setWinLossLoading(false);
    }
  }, []);

  const fetchEnforcement = useCallback(async () => {
    setEnforcementLoading(true);
    setEnforcementError(null);
    try {
      const res = await api.get("/policies/enforcement-log/?limit=100");
      const data = res.data;
      setEnforcement(Array.isArray(data) ? data : data.results ?? []);
    } catch (e) {
      setEnforcementError(
        e instanceof Error ? e.message : "Failed to load enforcement log"
      );
    } finally {
      setEnforcementLoading(false);
    }
  }, []);

  const fetchRecentRuns = useCallback(async () => {
    try {
      const res = await api.get("/analytics/agent-runs/?days=7");
      const data = res.data;
      setRecentRuns(Array.isArray(data) ? data : data.results ?? []);
    } catch {
      // non-critical
    }
  }, []);

  const fetchForecast = useCallback(async () => {
    try {
      const res = await api.get("/analytics/forecast/");
      const data = res.data;
      setForecastQuarters(Array.isArray(data) ? data : data.quarters ?? []);
    } catch {
      // non-critical — forecast chart shows stub state
    }
  }, []);

  const fetchGraphs = useCallback(async () => {
    try {
      const res = await orchestratorApi.get("/graphs");
      setGraphs(res.data?.graphs ?? []);
      // Auto-select the first graph
      if (res.data?.graphs?.length > 0 && !selectedGraph) {
        const first = res.data.graphs[0];
        setSelectedGraph(first.id);
        loadGraphMermaid(first.id);
      }
    } catch {
      // non-critical
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadGraphMermaid = async (graphId: string) => {
    setGraphLoading(true);
    setGraphMermaid("");
    setGraphTitle("");
    try {
      const res = await orchestratorApi.get(`/graphs/${graphId}/mermaid`);
      setGraphMermaid(res.data?.mermaid ?? "");
      setGraphTitle(res.data?.title ?? graphId);
    } catch {
      setGraphMermaid("");
    } finally {
      setGraphLoading(false);
    }
  };

  useEffect(() => {
    fetchAgentRuns();
    fetchWinLoss();
    fetchEnforcement();
    fetchRecentRuns();
    fetchForecast();
    fetchGraphs();
  }, [fetchAgentRuns, fetchWinLoss, fetchEnforcement, fetchRecentRuns, fetchForecast, fetchGraphs]);

  // --- Computed KPIs ---
  const winRate =
    winLoss.length > 0
      ? (winLoss.filter((r) => r.won).length / winLoss.length) * 100
      : null;

  // Precision@10: top 10 by confidence that resulted in a bid (submitted/awarded)
  const sortedByConf = [...winLoss]
    .filter((r) => r.ai_confidence !== null)
    .sort((a, b) => (b.ai_confidence ?? 0) - (a.ai_confidence ?? 0));
  const top10 = sortedByConf.slice(0, 10);
  const precision10 =
    top10.length > 0
      ? (top10.filter(
          (r) =>
            r.deal_stage === "submitted" || r.deal_stage === "awarded"
        ).length /
          top10.length) *
        100
      : null;

  // Avg proposal cycle time (stub — from agent run latency summation)
  const proposalRuns = agentRuns.filter(
    (r) => r.agent_name === "proposal_writer_agent"
  );
  const avgCycleMs =
    proposalRuns.length > 0
      ? proposalRuns
          .map((r) => r.latency_ms ?? 0)
          .reduce((a, b) => a + b, 0) / proposalRuns.length
      : null;
  const avgCycleDays =
    avgCycleMs !== null ? avgCycleMs / (1000 * 60 * 60 * 24) : null;

  // Override rate
  const overrideCount = agentRuns.filter((r) => r.override).length;
  const overrideRate =
    agentRuns.length > 0 ? (overrideCount / agentRuns.length) * 100 : null;

  // Group agent runs by agent name
  const runsByAgent: Record<string, AgentRun[]> = {};
  for (const run of agentRuns) {
    if (!runsByAgent[run.agent_name]) runsByAgent[run.agent_name] = [];
    runsByAgent[run.agent_name].push(run);
  }

  // Enforcement summary
  const allowedCount = enforcement.filter((e) => e.decision === "allowed").length;
  const hitlCount = enforcement.filter((e) => e.decision === "hitl_required").length;
  const blockedCount = enforcement.filter((e) => e.decision === "blocked").length;
  const totalEnforcement = enforcement.length;

  // Hallucination per agent (last 7 days)
  const hallucinationByAgent: Record<string, number> = {};
  for (const run of recentRuns) {
    hallucinationByAgent[run.agent_name] =
      (hallucinationByAgent[run.agent_name] ?? 0) +
      (run.hallucination_flags ?? 0);
  }
  const totalHallucinations = Object.values(hallucinationByAgent).reduce(
    (a, b) => a + b,
    0
  );
  const maxHallucinations = Math.max(
    ...Object.values(hallucinationByAgent),
    1
  );

  // Win/Loss scatter — filter to those with confidence score
  const scatterPoints = winLoss.filter((r) => r.ai_confidence !== null);

  const handleRefresh = () => {
    fetchAgentRuns();
    fetchWinLoss();
    fetchEnforcement();
    fetchRecentRuns();
    fetchForecast();
  };

  return (
    <div className="space-y-6 p-6">
      {/* 1. Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-100 rounded-lg">
            <Brain className="h-6 w-6 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              AI Command Center
            </h1>
            <p className="text-sm text-gray-500 flex items-center gap-1">
              <Cpu className="h-3.5 w-3.5" />
              Executive AI performance &amp; trust metrics
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh}>
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
          Refresh All
        </Button>
      </div>

      {/* 2. KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard
          title="Win Rate"
          value={winLossLoading ? "..." : formatPct(winRate)}
          subtitle={
            winLoss.length > 0
              ? `${winLoss.filter((r) => r.won).length} wins / ${winLoss.length} bids`
              : "No bid data"
          }
          icon={<TrendingUp className="h-5 w-5 text-green-500" />}
          colorClass="text-green-700"
        />
        <KpiCard
          title="Precision@10"
          value={winLossLoading ? "..." : formatPct(precision10)}
          subtitle="Top-10 ranked opps resulting in a bid"
          icon={<Target className="h-5 w-5 text-blue-500" />}
          colorClass="text-blue-700"
        />
        <KpiCard
          title="Avg Proposal Cycle"
          value={
            agentRunsLoading
              ? "..."
              : avgCycleDays !== null
              ? formatDays(avgCycleDays)
              : "—"
          }
          subtitle="Intake to submission"
          icon={<Clock className="h-5 w-5 text-purple-500" />}
          colorClass="text-purple-700"
        />
        <KpiCard
          title="AI Override Rate"
          value={agentRunsLoading ? "..." : formatPct(overrideRate)}
          subtitle={
            agentRuns.length > 0
              ? `${overrideCount} overrides / ${agentRuns.length} actions`
              : "No agent runs"
          }
          icon={<Users className="h-5 w-5 text-amber-500" />}
          colorClass={
            overrideRate !== null && overrideRate > 20
              ? "text-red-700"
              : "text-amber-700"
          }
        />
      </div>

      {/* 3. Agent Performance Grid */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Cpu className="h-4 w-4 text-indigo-500" />
            Agent Performance Grid
          </CardTitle>
          <CardDescription>
            Last 30 runs per agent — success rate, latency, cost, overrides
          </CardDescription>
        </CardHeader>
        <CardContent>
          {agentRunsLoading ? (
            <div className="flex items-center gap-2 text-gray-500 py-6">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading agent runs...</span>
            </div>
          ) : agentRunsError ? (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {agentRunsError}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {KNOWN_AGENTS.map((agentName) => (
                <AgentScorecard
                  key={agentName}
                  agentName={agentName}
                  runs={runsByAgent[agentName] ?? []}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 3b. LangGraph Workflow Visualization */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-purple-500" />
            Agent Workflow Graphs
          </CardTitle>
          <CardDescription>
            Visual diagrams of LangGraph workflows showing how agents are designed and connected
          </CardDescription>
        </CardHeader>
        <CardContent>
          {graphs.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-6">
              No graph visualizations available — ensure the AI Orchestrator is running
            </p>
          ) : (
            <div className="space-y-4">
              {/* Graph selector tabs */}
              <div className="flex flex-wrap gap-2">
                {graphs.map((g) => (
                  <Button
                    key={g.id}
                    size="sm"
                    variant={selectedGraph === g.id ? "default" : "outline"}
                    onClick={() => {
                      setSelectedGraph(g.id);
                      setShowGraphSource(false);
                      loadGraphMermaid(g.id);
                    }}
                    className="text-xs"
                  >
                    {g.title}
                  </Button>
                ))}
              </div>

              {/* Graph description */}
              {selectedGraph && (
                <p className="text-xs text-muted-foreground">
                  {graphs.find((g) => g.id === selectedGraph)?.description}
                </p>
              )}

              {/* Graph content */}
              {graphLoading ? (
                <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" /> Loading graph...
                </div>
              ) : graphMermaid ? (
                <div className="space-y-2">
                  <InlineMermaidRenderer code={graphMermaid} id={selectedGraph ?? "graph"} />
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-xs gap-1"
                      onClick={() => setShowGraphSource((v) => !v)}
                    >
                      {showGraphSource ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                      {showGraphSource ? "Hide" : "Show"} Mermaid Source
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-xs gap-1"
                      onClick={() => navigator.clipboard.writeText(graphMermaid)}
                    >
                      <Copy className="h-3 w-3" /> Copy
                    </Button>
                  </div>
                  {showGraphSource && (
                    <pre className="overflow-x-auto rounded-lg bg-muted p-4 text-xs leading-relaxed text-foreground/80 border border-border max-h-[300px] overflow-y-auto">
                      <code>{graphMermaid}</code>
                    </pre>
                  )}
                </div>
              ) : selectedGraph ? (
                <p className="text-sm text-muted-foreground text-center py-6">
                  Could not load graph visualization
                </p>
              ) : null}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 4. Win Rate vs AI Confidence Scatter */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart2 className="h-4 w-4 text-blue-500" />
            Win Rate vs AI Confidence
          </CardTitle>
          <CardDescription>
            Scatter plot — X: AI confidence score, Y: Won (1) / Lost (0). Color
            by deal stage.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {winLossLoading ? (
            <div className="flex items-center gap-2 text-gray-500 py-6">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading win/loss data...</span>
            </div>
          ) : winLossError ? (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {winLossError}
            </div>
          ) : scatterPoints.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <BarChart2 className="h-10 w-10 mb-2 opacity-30" />
              <p className="text-sm">
                No win/loss data with confidence scores available
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <svg
                width="100%"
                viewBox="0 0 520 240"
                preserveAspectRatio="xMidYMid meet"
              >
                {/* Axes */}
                <line
                  x1="48"
                  y1="20"
                  x2="48"
                  y2="200"
                  stroke="#e5e7eb"
                  strokeWidth="1"
                />
                <line
                  x1="48"
                  y1="200"
                  x2="508"
                  y2="200"
                  stroke="#e5e7eb"
                  strokeWidth="1"
                />

                {/* Y axis labels */}
                <text x="42" y="108" textAnchor="end" fontSize="9" fill="#9ca3af">
                  Lost (0)
                </text>
                <text x="42" y="68" textAnchor="end" fontSize="9" fill="#9ca3af">
                  Won (1)
                </text>
                {/* Y gridlines */}
                <line
                  x1="48"
                  y1="105"
                  x2="508"
                  y2="105"
                  stroke="#f3f4f6"
                  strokeWidth="1"
                  strokeDasharray="4,4"
                />
                <line
                  x1="48"
                  y1="65"
                  x2="508"
                  y2="65"
                  stroke="#f3f4f6"
                  strokeWidth="1"
                  strokeDasharray="4,4"
                />

                {/* X axis labels */}
                {[0, 0.25, 0.5, 0.75, 1.0].map((v) => {
                  const x = 48 + v * 460;
                  return (
                    <g key={v}>
                      <line
                        x1={x}
                        y1="200"
                        x2={x}
                        y2="205"
                        stroke="#9ca3af"
                        strokeWidth="1"
                      />
                      <text
                        x={x}
                        y="215"
                        textAnchor="middle"
                        fontSize="8"
                        fill="#9ca3af"
                      >
                        {v.toFixed(2)}
                      </text>
                    </g>
                  );
                })}

                {/* Axis labels */}
                <text
                  x="278"
                  y="230"
                  textAnchor="middle"
                  fontSize="9"
                  fill="#6b7280"
                >
                  AI Confidence Score
                </text>
                <text
                  x="10"
                  y="110"
                  textAnchor="middle"
                  fontSize="9"
                  fill="#6b7280"
                  transform="rotate(-90 10 110)"
                >
                  Outcome
                </text>

                {/* Scatter points */}
                {scatterPoints.map((pt, i) => {
                  const x = 48 + (pt.ai_confidence ?? 0) * 460;
                  // Won = y around 65, Lost = y around 105, with jitter
                  const baseY = pt.won ? 65 : 105;
                  const jitter = (Math.sin(i * 7.3) * 12);
                  const y = baseY + jitter;
                  const color = stageColor(pt.deal_stage);
                  return (
                    <circle
                      key={pt.id ?? i}
                      cx={x}
                      cy={y}
                      r="4"
                      fill={color}
                      fillOpacity="0.7"
                      stroke={color}
                      strokeWidth="0.5"
                    />
                  );
                })}
              </svg>

              {/* Legend */}
              <div className="flex items-center gap-4 flex-wrap text-xs text-gray-500 mt-2 px-12">
                {["qualification", "proposal", "review", "submitted", "awarded", "lost"].map(
                  (stage) => (
                    <div key={stage} className="flex items-center gap-1">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: stageColor(stage) }}
                      />
                      <span className="capitalize">{stage}</span>
                    </div>
                  )
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 5. Policy Enforcement Summary */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-500" />
            Policy Enforcement Summary
          </CardTitle>
          <CardDescription>
            Breakdown of the last 100 enforcement decisions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {enforcementLoading ? (
            <div className="flex items-center gap-2 text-gray-500 py-4">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading enforcement data...</span>
            </div>
          ) : enforcementError ? (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {enforcementError}
            </div>
          ) : totalEnforcement === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">
              No enforcement events recorded
            </p>
          ) : (
            <div className="grid grid-cols-3 gap-4">
              <div className="flex flex-col items-center rounded-xl border border-green-200 bg-green-50 py-6 px-4">
                <CheckCircle className="h-8 w-8 text-green-500 mb-2" />
                <p className="text-4xl font-bold text-green-700">
                  {allowedCount}
                </p>
                <p className="text-sm font-semibold text-green-600 mt-1">
                  Allowed
                </p>
                <p className="text-xs text-green-500 mt-0.5">
                  {totalEnforcement > 0
                    ? `${((allowedCount / totalEnforcement) * 100).toFixed(0)}%`
                    : "0%"}{" "}
                  of decisions
                </p>
              </div>
              <div className="flex flex-col items-center rounded-xl border border-amber-200 bg-amber-50 py-6 px-4">
                <AlertCircle className="h-8 w-8 text-amber-500 mb-2" />
                <p className="text-4xl font-bold text-amber-700">
                  {hitlCount}
                </p>
                <p className="text-sm font-semibold text-amber-600 mt-1">
                  HITL Required
                </p>
                <p className="text-xs text-amber-500 mt-0.5">
                  {totalEnforcement > 0
                    ? `${((hitlCount / totalEnforcement) * 100).toFixed(0)}%`
                    : "0%"}{" "}
                  of decisions
                </p>
              </div>
              <div className="flex flex-col items-center rounded-xl border border-red-200 bg-red-50 py-6 px-4">
                <MinusCircle className="h-8 w-8 text-red-500 mb-2" />
                <p className="text-4xl font-bold text-red-700">
                  {blockedCount}
                </p>
                <p className="text-sm font-semibold text-red-600 mt-1">
                  Blocked
                </p>
                <p className="text-xs text-red-500 mt-0.5">
                  {totalEnforcement > 0
                    ? `${((blockedCount / totalEnforcement) * 100).toFixed(0)}%`
                    : "0%"}{" "}
                  of decisions
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 6. Hallucination Monitor */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-500" />
            Hallucination Monitor
          </CardTitle>
          <CardDescription>
            Hallucination flags per agent over the last 7 days
          </CardDescription>
        </CardHeader>
        <CardContent>
          {totalHallucinations === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-green-600">
              <CheckCircle className="h-10 w-10 mb-2" />
              <p className="font-semibold">0 hallucinations detected</p>
              <p className="text-xs text-gray-400 mt-1">
                All agents operating cleanly over the last 7 days
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {KNOWN_AGENTS.map((agent) => {
                const count = hallucinationByAgent[agent] ?? 0;
                const pct = (count / maxHallucinations) * 100;
                const agentLabel = agent
                  .replace(/_agent$/, "")
                  .split("_")
                  .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                  .join(" ");
                return (
                  <div key={agent} className="flex items-center gap-3">
                    <span className="text-sm text-gray-600 w-40 flex-shrink-0">
                      {agentLabel}
                    </span>
                    <div className="flex-1 h-5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          count === 0
                            ? "bg-green-400"
                            : count <= 2
                            ? "bg-amber-400"
                            : "bg-red-500"
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span
                      className={`text-sm font-bold w-6 text-right ${
                        count === 0
                          ? "text-green-600"
                          : count <= 2
                          ? "text-amber-600"
                          : "text-red-600"
                      }`}
                    >
                      {count}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 7. Revenue vs AI Forecast Accuracy */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <ForecastChart quarters={forecastQuarters} />

        {/* Risk Score stub */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Pipeline Risk Assessment
            </CardTitle>
            <CardDescription>
              Aggregate risk profile for active pipeline
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RiskScoreDisplay riskScore={riskScore} showDetails={false} />
          </CardContent>
        </Card>
      </div>

      {/* 8. Autonomy Maturity Status */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Brain className="h-4 w-4 text-indigo-500" />
            Autonomy Maturity Roadmap
          </CardTitle>
          <CardDescription>
            Progress toward full AI autonomy — Year 1 through Year 3
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Timeline */}
          <div className="relative pt-2 pb-8">
            {/* Track */}
            <div className="absolute top-5 left-0 right-0 h-2 bg-gray-200 rounded-full" />

            {/* Progress fill — Year 1 complete, starting Year 2 */}
            <div
              className="absolute top-5 left-0 h-2 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"
              style={{ width: "40%" }}
            />

            {/* Milestones */}
            {[
              {
                pct: 0,
                label: "Start",
                sublabel: "L0 Assistive",
                color: "bg-slate-400",
              },
              {
                pct: 33,
                label: "Year 1",
                sublabel: "Mostly L1",
                color: "bg-blue-500",
                current: true,
              },
              {
                pct: 66,
                label: "Year 2",
                sublabel: "Selective L2",
                color: "bg-amber-400",
              },
              {
                pct: 100,
                label: "Year 3",
                sublabel: "Controlled L3",
                color: "bg-red-400",
              },
            ].map((milestone) => (
              <div
                key={milestone.label}
                className="absolute"
                style={{ left: `${milestone.pct}%`, top: 0 }}
              >
                {/* Dot */}
                <div
                  className={`w-5 h-5 rounded-full border-2 border-white shadow ${milestone.color} ${
                    milestone.current
                      ? "ring-2 ring-indigo-400 ring-offset-1"
                      : ""
                  }`}
                />
                {/* Label */}
                <div
                  className={`absolute mt-4 ${
                    milestone.pct === 100
                      ? "-translate-x-full"
                      : milestone.pct === 0
                      ? ""
                      : "-translate-x-1/2"
                  }`}
                  style={{ top: "100%", whiteSpace: "nowrap" }}
                >
                  <p
                    className={`text-xs font-bold ${
                      milestone.current ? "text-indigo-700" : "text-gray-600"
                    }`}
                  >
                    {milestone.label}
                    {milestone.current && " ← Now"}
                  </p>
                  <p className="text-xs text-gray-400">{milestone.sublabel}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Summary row */}
          <div className="grid grid-cols-3 gap-3 pt-2">
            {[
              {
                year: "Year 1",
                status: "In Progress",
                desc: "L1 as default for all agents. Human approves every submission.",
                statusColor: "text-blue-600",
                bg: "bg-blue-50 border-blue-200",
              },
              {
                year: "Year 2",
                status: "Planned",
                desc: "Selective L2 for low-risk agencies. Conditional auto-advance enabled.",
                statusColor: "text-amber-600",
                bg: "bg-amber-50 border-amber-200",
              },
              {
                year: "Year 3",
                status: "Future",
                desc: "Controlled L3 auto-bid under $5M with confidence gate > 0.85.",
                statusColor: "text-red-600",
                bg: "bg-red-50 border-red-200",
              },
            ].map((item) => (
              <div
                key={item.year}
                className={`rounded-lg border p-3 ${item.bg}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-bold text-gray-700">{item.year}</p>
                  <p className={`text-xs font-semibold ${item.statusColor}`}>
                    {item.status}
                  </p>
                </div>
                <p className="text-xs text-gray-500">{item.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
