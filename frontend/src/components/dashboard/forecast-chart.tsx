"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart2 } from "lucide-react";

interface ForecastQuarter {
  quarter: string;           // e.g. "2026-Q1"
  pipeline_value: number;
  weighted_value: number;    // pipeline_value * win_probability
  deal_count: number;
  low?: number;              // 70% of weighted
  high?: number;             // 135% of weighted
}

interface ForecastChartProps {
  quarters: ForecastQuarter[];
}

function formatValue(v: number): string {
  if (v >= 1_000_000_000) return `$${(v / 1_000_000_000).toFixed(1)}B`;
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

function buildDefaultQuarters(): ForecastQuarter[] {
  const now = new Date();
  const quarters: ForecastQuarter[] = [];
  for (let i = 0; i < 4; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() + i * 3, 1);
    const q = Math.floor(d.getMonth() / 3) + 1;
    const weighted = 0;
    quarters.push({
      quarter: `${d.getFullYear()}-Q${q}`,
      pipeline_value: 0,
      weighted_value: weighted,
      deal_count: 0,
      low: weighted * 0.7,
      high: weighted * 1.35,
    });
  }
  return quarters;
}

export function ForecastChart({ quarters }: ForecastChartProps) {
  const data = quarters && quarters.length > 0 ? quarters : buildDefaultQuarters();

  // Enrich with low/high if not provided
  const enriched = data.map((q) => ({
    ...q,
    low: q.low ?? q.weighted_value * 0.7,
    high: q.high ?? q.weighted_value * 1.35,
  }));

  const maxVal = Math.max(...enriched.map((q) => q.high ?? q.weighted_value), 1);
  const totalWeighted = enriched.reduce((s, q) => s + q.weighted_value, 0);
  const totalPipeline = enriched.reduce((s, q) => s + q.pipeline_value, 0);

  const svgW = 400;
  const svgH = 160;
  const padL = 48;
  const padR = 12;
  const padT = 12;
  const padB = 32;
  const innerW = svgW - padL - padR;
  const innerH = svgH - padT - padB;

  const n = enriched.length;
  const groupW = innerW / n;
  const barW = groupW * 0.55;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <BarChart2 className="h-4 w-4 text-blue-500" /> Revenue Forecast (4 Quarters)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {totalPipeline === 0 ? (
          <div className="flex items-center justify-center h-24 text-muted-foreground text-sm">
            No pipeline data to forecast
          </div>
        ) : (
          <>
            <svg width="100%" viewBox={`0 0 ${svgW} ${svgH}`} preserveAspectRatio="xMidYMid meet">
              {/* Y-axis grid */}
              {[0, 25, 50, 75, 100].map((pct) => {
                const y = padT + innerH - (pct / 100) * innerH;
                const val = (pct / 100) * maxVal;
                return (
                  <g key={pct}>
                    <line x1={padL} y1={y} x2={padL + innerW} y2={y} stroke="#e5e7eb" strokeWidth={1} />
                    <text x={padL - 4} y={y + 3} textAnchor="end" fontSize={7} fill="#9ca3af">
                      {formatValue(val)}
                    </text>
                  </g>
                );
              })}

              {enriched.map((q, i) => {
                const x = padL + i * groupW + groupW / 2 - barW / 2;
                const pipeH = (q.pipeline_value / maxVal) * innerH;
                const weightH = (q.weighted_value / maxVal) * innerH;
                const highH = ((q.high ?? q.weighted_value) / maxVal) * innerH;
                const lowY = padT + innerH - ((q.low ?? 0) / maxVal) * innerH;
                const labelX = padL + i * groupW + groupW / 2;

                return (
                  <g key={q.quarter}>
                    {/* Pipeline bar (light blue, full width) */}
                    <rect
                      x={x}
                      y={padT + innerH - pipeH}
                      width={barW}
                      height={pipeH}
                      fill="#bfdbfe"
                      rx={2}
                    />
                    {/* Weighted bar (darker blue, 60% width, centered) */}
                    <rect
                      x={x + barW * 0.2}
                      y={padT + innerH - weightH}
                      width={barW * 0.6}
                      height={weightH}
                      fill="#3b82f6"
                      rx={2}
                    />
                    {/* High/low range as whisker */}
                    <line
                      x1={labelX}
                      y1={padT + innerH - highH}
                      x2={labelX}
                      y2={lowY}
                      stroke="#1d4ed8"
                      strokeWidth={1.5}
                    />
                    <line x1={labelX - 4} y1={padT + innerH - highH} x2={labelX + 4} y2={padT + innerH - highH} stroke="#1d4ed8" strokeWidth={1.5} />
                    <line x1={labelX - 4} y1={lowY} x2={labelX + 4} y2={lowY} stroke="#1d4ed8" strokeWidth={1.5} />

                    {/* Quarter label */}
                    <text x={labelX} y={padT + innerH + 12} textAnchor="middle" fontSize={8} fill="#6b7280">
                      {q.quarter}
                    </text>
                    {/* Deal count */}
                    <text x={labelX} y={padT + innerH + 22} textAnchor="middle" fontSize={7} fill="#9ca3af">
                      {q.deal_count}d
                    </text>
                  </g>
                );
              })}
            </svg>

            {/* Legend */}
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <div className="w-8 h-3 rounded" style={{ backgroundColor: "#bfdbfe" }} />
                Pipeline value
              </div>
              <div className="flex items-center gap-1">
                <div className="w-8 h-3 rounded" style={{ backgroundColor: "#3b82f6" }} />
                Weighted (× win prob)
              </div>
              <div className="flex items-center gap-1">
                <div className="w-0.5 h-4 bg-blue-700 relative">
                  <div className="absolute -top-0.5 -left-1 w-2 border-t border-blue-700" />
                  <div className="absolute -bottom-0.5 -left-1 w-2 border-t border-blue-700" />
                </div>
                <span className="ml-1">Range</span>
              </div>
            </div>

            {/* Summary */}
            <div className="grid grid-cols-2 gap-3 pt-2 border-t">
              <div className="text-center">
                <p className="text-xs text-muted-foreground">Total Pipeline</p>
                <p className="font-semibold text-sm">{formatValue(totalPipeline)}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-muted-foreground">Expected Revenue</p>
                <p className="font-bold text-blue-700">{formatValue(totalWeighted)}</p>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
