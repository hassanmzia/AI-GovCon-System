"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Target } from "lucide-react";

interface WinProbabilityChartProps {
  scenarios: Array<{
    name: string;
    total_price: number;
    probability_of_win: number;
    margin_pct?: number;
  }>;
  selectedScenarioId?: string;
}

function formatValue(v: number): string {
  if (v >= 1_000_000_000) return `$${(v / 1_000_000_000).toFixed(1)}B`;
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

function getWinColor(prob: number): string {
  if (prob >= 65) return "#10b981"; // green
  if (prob >= 40) return "#f59e0b"; // amber
  return "#ef4444"; // red
}

function getWinLabel(prob: number): string {
  if (prob >= 70) return "Strong";
  if (prob >= 50) return "Competitive";
  if (prob >= 35) return "Marginal";
  return "Unlikely";
}

export function WinProbabilityChart({ scenarios }: WinProbabilityChartProps) {
  if (!scenarios || scenarios.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Target className="h-4 w-4 text-blue-500" /> Win Probability
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-24 text-muted-foreground text-sm">
            No scenarios to compare
          </div>
        </CardContent>
      </Card>
    );
  }

  const svgW = 380;
  const svgH = 160;
  const padL = 80;
  const padR = 20;
  const padT = 16;
  const padB = 28;
  const innerW = svgW - padL - padR;
  const innerH = svgH - padT - padB;

  const sortedByPrice = [...scenarios].sort((a, b) => a.total_price - b.total_price);
  const maxPrice = Math.max(...sortedByPrice.map((s) => s.total_price), 1);
  const barHeight = Math.max(8, Math.floor((innerH / sortedByPrice.length) * 0.65));
  const step = innerH / sortedByPrice.length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Target className="h-4 w-4 text-blue-500" /> Win Probability by Price
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Bar chart: price on x-axis, scenario on y-axis, colored by win prob */}
        <svg width="100%" viewBox={`0 0 ${svgW} ${svgH}`} preserveAspectRatio="xMidYMid meet">
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map((pct) => {
            const x = padL + (pct / 100) * innerW;
            return (
              <g key={pct}>
                <line x1={x} y1={padT} x2={x} y2={padT + innerH} stroke="#e5e7eb" strokeWidth={1} />
                <text x={x} y={padT + innerH + 12} textAnchor="middle" fontSize={7} fill="#9ca3af">
                  {pct}%
                </text>
              </g>
            );
          })}
          <text x={padL + innerW / 2} y={svgH} textAnchor="middle" fontSize={8} fill="#6b7280">
            Price as % of max scenario
          </text>

          {sortedByPrice.map((s, i) => {
            const pricePct = maxPrice > 0 ? (s.total_price / maxPrice) * 100 : 0;
            const barW = (pricePct / 100) * innerW;
            const y = padT + i * step + step / 2 - barHeight / 2;
            const color = getWinColor(s.probability_of_win);
            const labelX = padL - 4;
            const labelY = padT + i * step + step / 2;

            return (
              <g key={s.name}>
                <text x={labelX} y={labelY + 3} textAnchor="end" fontSize={7} fill="#374151">
                  {s.name.length > 10 ? s.name.slice(0, 10) + "…" : s.name}
                </text>
                {/* Price bar */}
                <rect x={padL} y={y} width={Math.max(barW, 2)} height={barHeight} fill={color} opacity={0.8} rx={2} />
                {/* Win prob label inside/after bar */}
                {barW > 30 && (
                  <text x={padL + barW - 4} y={labelY + 3} textAnchor="end" fontSize={7} fill="white" fontWeight="bold">
                    {s.probability_of_win.toFixed(0)}%
                  </text>
                )}
                {barW <= 30 && (
                  <text x={padL + barW + 4} y={labelY + 3} textAnchor="start" fontSize={7} fill={color} fontWeight="bold">
                    {s.probability_of_win.toFixed(0)}%
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Scenario summary table */}
        <div className="space-y-1">
          {sortedByPrice.map((s) => (
            <div
              key={s.name}
              className="flex items-center justify-between text-xs px-2 py-1 rounded"
              style={{ backgroundColor: getWinColor(s.probability_of_win) + "15" }}
            >
              <span className="font-medium text-foreground">{s.name}</span>
              <div className="flex items-center gap-3 text-muted-foreground">
                <span>{formatValue(s.total_price)}</span>
                {s.margin_pct != null && <span>{s.margin_pct.toFixed(1)}% margin</span>}
                <span
                  className="font-semibold px-1.5 py-0.5 rounded text-white text-[10px]"
                  style={{ backgroundColor: getWinColor(s.probability_of_win) }}
                >
                  {getWinLabel(s.probability_of_win)} · {s.probability_of_win.toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground pt-1">
          {[
            { color: "#10b981", label: "Strong (≥65%)" },
            { color: "#f59e0b", label: "Competitive (40-64%)" },
            { color: "#ef4444", label: "Marginal (<40%)" },
          ].map((l) => (
            <div key={l.label} className="flex items-center gap-1">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: l.color }} />
              {l.label}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
