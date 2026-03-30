"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Bot, AlertTriangle, TrendingUp } from "lucide-react";

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
}

interface AgentScorecardProps {
  agentName: string;
  runs: AgentRun[];
}

function formatLatency(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms)}ms`;
}

function formatCost(usd: number): string {
  if (usd < 0.01) return `$${(usd * 100).toFixed(2)}¢`;
  return `$${usd.toFixed(4)}`;
}

function agentDisplayName(name: string): string {
  return name
    .replace(/_agent$/, "")
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function AgentScorecard({ agentName, runs }: AgentScorecardProps) {
  // Take last 30 runs
  const last30 = runs.slice(-30);

  // Compute stats
  const totalRuns = last30.length;
  const successRuns = last30.filter((r) => r.success === true).length;
  const successRate =
    totalRuns > 0 ? Math.round((successRuns / totalRuns) * 100) : 0;

  const latencies = last30
    .map((r) => r.latency_ms)
    .filter((v): v is number => v !== null);
  const avgLatency =
    latencies.length > 0
      ? latencies.reduce((a, b) => a + b, 0) / latencies.length
      : null;

  const costs = last30
    .map((r) => r.cost_usd)
    .filter((v): v is number => v !== null);
  const avgCost =
    costs.length > 0
      ? costs.reduce((a, b) => a + b, 0) / costs.length
      : null;

  const confidences = last30
    .map((r) => r.confidence)
    .filter((v): v is number => v !== null);
  const avgConfidence =
    confidences.length > 0
      ? confidences.reduce((a, b) => a + b, 0) / confidences.length
      : null;

  const overrideRuns = last30.filter((r) => r.override).length;
  const overrideRate =
    totalRuns > 0 ? Math.round((overrideRuns / totalRuns) * 100) : 0;

  const totalHallucinations = last30.reduce(
    (sum, r) => sum + (r.hallucination_flags ?? 0),
    0
  );

  // Status color based on success rate
  const statusColor =
    successRate >= 90
      ? { border: "border-green-400", header: "bg-green-50 dark:bg-green-950/30", dot: "bg-green-500", text: "text-green-700 dark:text-green-400" }
      : successRate >= 70
      ? { border: "border-amber-400", header: "bg-amber-50 dark:bg-amber-950/30", dot: "bg-amber-500", text: "text-amber-700 dark:text-amber-400" }
      : { border: "border-red-400", header: "bg-red-50 dark:bg-red-950/30", dot: "bg-red-500", text: "text-red-700 dark:text-red-400" };

  // Trend line: compute success rate in chunks of 6 runs
  const chunkSize = 6;
  const trendPoints: number[] = [];
  for (let i = 0; i < last30.length; i += chunkSize) {
    const chunk = last30.slice(i, i + chunkSize);
    const chunkSuccess = chunk.filter((r) => r.success === true).length;
    trendPoints.push(chunk.length > 0 ? chunkSuccess / chunk.length : 0);
  }

  // SVG trend line
  const svgW = 120;
  const svgH = 36;
  const n = trendPoints.length;
  const trendPath =
    n < 2
      ? null
      : trendPoints
          .map((val, i) => {
            const x = (i / (n - 1)) * svgW;
            const y = svgH - val * svgH;
            return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
          })
          .join(" ");

  // Last 5 runs dots
  const last5 = runs.slice(-5);

  return (
    <Card className={`border-2 ${statusColor.border}`}>
      <CardHeader className={`pb-2 ${statusColor.header} rounded-t-lg`}>
        <CardTitle className="text-sm font-semibold flex items-center gap-2 text-foreground">
          <Bot className="h-4 w-4 text-muted-foreground" />
          <span>{agentDisplayName(agentName)}</span>
          <div className={`ml-auto w-2.5 h-2.5 rounded-full ${statusColor.dot}`} />
        </CardTitle>
      </CardHeader>

      <CardContent className="pt-3 space-y-3">
        {totalRuns === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-2">No runs recorded</p>
        ) : (
          <>
            {/* Success Rate + Trend */}
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Success Rate</p>
                <p className={`text-2xl font-bold ${statusColor.text}`}>
                  {successRate}%
                </p>
                <p className="text-xs text-muted-foreground/70">{totalRuns} runs</p>
              </div>

              {/* SVG Trend Line */}
              {trendPath && (
                <div className="flex flex-col items-end gap-1">
                  <div className="flex items-center gap-1 text-xs text-muted-foreground/70">
                    <TrendingUp className="h-3 w-3" />
                    <span>trend</span>
                  </div>
                  <svg
                    width={svgW}
                    height={svgH}
                    viewBox={`0 0 ${svgW} ${svgH}`}
                    className="overflow-visible"
                  >
                    <defs>
                      <linearGradient
                        id={`grad-${agentName}`}
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="0%"
                          stopColor={
                            successRate >= 90
                              ? "#16a34a"
                              : successRate >= 70
                              ? "#d97706"
                              : "#dc2626"
                          }
                          stopOpacity="0.2"
                        />
                        <stop offset="100%" stopColor="transparent" stopOpacity="0" />
                      </linearGradient>
                    </defs>
                    {/* Grid lines */}
                    <line x1="0" y1="0" x2={svgW} y2="0" className="stroke-border" strokeWidth="1" />
                    <line x1="0" y1={svgH / 2} x2={svgW} y2={svgH / 2} className="stroke-border" strokeWidth="1" />
                    <line x1="0" y1={svgH} x2={svgW} y2={svgH} className="stroke-border" strokeWidth="1" />
                    {/* Area fill */}
                    <path
                      d={`${trendPath} L ${svgW} ${svgH} L 0 ${svgH} Z`}
                      fill={`url(#grad-${agentName})`}
                    />
                    {/* Line */}
                    <path
                      d={trendPath}
                      fill="none"
                      stroke={
                        successRate >= 90
                          ? "#16a34a"
                          : successRate >= 70
                          ? "#d97706"
                          : "#dc2626"
                      }
                      strokeWidth="1.5"
                      strokeLinejoin="round"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
              )}
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded bg-muted px-2 py-1.5">
                <p className="text-muted-foreground/70">Avg Latency</p>
                <p className="font-semibold text-foreground">
                  {avgLatency !== null ? formatLatency(avgLatency) : "—"}
                </p>
              </div>
              <div className="rounded bg-muted px-2 py-1.5">
                <p className="text-muted-foreground/70">Avg Cost</p>
                <p className="font-semibold text-foreground">
                  {avgCost !== null ? formatCost(avgCost) : "—"}
                </p>
              </div>
              <div className="rounded bg-muted px-2 py-1.5">
                <p className="text-muted-foreground/70">Avg Confidence</p>
                <p className="font-semibold text-foreground">
                  {avgConfidence !== null
                    ? `${Math.round(avgConfidence * 100)}%`
                    : "—"}
                </p>
              </div>
              <div className="rounded bg-muted px-2 py-1.5">
                <p className="text-muted-foreground/70">Override Rate</p>
                <p className="font-semibold text-foreground">{overrideRate}%</p>
              </div>
            </div>

            {/* Hallucination Flags */}
            <div
              className={`flex items-center gap-2 rounded px-2 py-1.5 text-xs ${
                totalHallucinations > 0
                  ? "bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              <AlertTriangle
                className={`h-3.5 w-3.5 ${
                  totalHallucinations > 0 ? "text-red-600 dark:text-red-400" : "text-muted-foreground/70"
                }`}
              />
              <span className="font-medium">
                {totalHallucinations > 0
                  ? `${totalHallucinations} hallucination flag${totalHallucinations > 1 ? "s" : ""}`
                  : "No hallucination flags"}
              </span>
            </div>

            {/* Last 5 Runs Dots */}
            {last5.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground/70">Last 5 runs:</span>
                <div className="flex items-center gap-1">
                  {last5.map((run, i) => {
                    const dotColor = run.override
                      ? "bg-amber-400 border-amber-500"
                      : run.success === true
                      ? "bg-green-500 border-green-600"
                      : "bg-red-500 border-red-600";
                    const title = run.override
                      ? "Overridden"
                      : run.success === true
                      ? "Success"
                      : "Failed";
                    return (
                      <div
                        key={i}
                        title={title}
                        className={`w-3 h-3 rounded-full border ${dotColor}`}
                      />
                    );
                  })}
                </div>
                <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground/70">
                  <span className="flex items-center gap-0.5">
                    <div className="w-2 h-2 rounded-full bg-green-500" /> ok
                  </span>
                  <span className="flex items-center gap-0.5">
                    <div className="w-2 h-2 rounded-full bg-amber-400" /> override
                  </span>
                  <span className="flex items-center gap-0.5">
                    <div className="w-2 h-2 rounded-full bg-red-500" /> fail
                  </span>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
