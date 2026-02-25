"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity } from "lucide-react";

interface SensitivityChartProps {
  basePrice: number;
  baseProbability: number;
  /** Percentage deltas to test, e.g. [-20, -15, -10, -5, 0, 5, 10, 15, 20] */
  deltas?: number[];
  /**
   * Elasticity: how many pct points of win probability change per 1% price change.
   * Negative means higher price → lower win probability.
   * Default: -1.5 (typical GovCon best-value environment)
   */
  elasticity?: number;
}

function formatValue(v: number): string {
  if (v >= 1_000_000_000) return `$${(v / 1_000_000_000).toFixed(1)}B`;
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

function clamp(v: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, v));
}

function probColor(p: number): string {
  if (p >= 65) return "#10b981";
  if (p >= 40) return "#f59e0b";
  return "#ef4444";
}

export function SensitivityChart({
  basePrice,
  baseProbability,
  deltas = [-20, -15, -10, -5, 0, 5, 10, 15, 20],
  elasticity = -1.5,
}: SensitivityChartProps) {
  const points = deltas.map((d) => ({
    delta: d,
    price: basePrice * (1 + d / 100),
    probability: clamp(baseProbability + elasticity * d, 2, 98),
  }));

  const svgW = 400;
  const svgH = 160;
  const padL = 50;
  const padR = 16;
  const padT = 12;
  const padB = 32;
  const innerW = svgW - padL - padR;
  const innerH = svgH - padT - padB;
  const n = points.length;

  const xScale = (i: number) => padL + (i / (n - 1)) * innerW;
  const yScale = (p: number) => padT + innerH - (p / 100) * innerH;

  // Build SVG path
  const pathD = points
    .map((pt, i) => `${i === 0 ? "M" : "L"} ${xScale(i).toFixed(1)} ${yScale(pt.probability).toFixed(1)}`)
    .join(" ");

  // Baseline index
  const baseIdx = points.findIndex((p) => p.delta === 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Activity className="h-4 w-4 text-purple-500" /> Price Sensitivity Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <svg width="100%" viewBox={`0 0 ${svgW} ${svgH}`} preserveAspectRatio="xMidYMid meet">
          {/* Horizontal grid lines */}
          {[0, 25, 50, 75, 100].map((p) => (
            <g key={p}>
              <line x1={padL} y1={yScale(p)} x2={padL + innerW} y2={yScale(p)} stroke="#e5e7eb" strokeWidth={1} />
              <text x={padL - 4} y={yScale(p) + 3} textAnchor="end" fontSize={8} fill="#9ca3af">
                {p}%
              </text>
            </g>
          ))}

          {/* 50% reference */}
          <line x1={padL} y1={yScale(50)} x2={padL + innerW} y2={yScale(50)} stroke="#d1d5db" strokeWidth={1.5} strokeDasharray="4 2" />

          {/* Baseline vertical */}
          {baseIdx >= 0 && (
            <line
              x1={xScale(baseIdx)}
              y1={padT}
              x2={xScale(baseIdx)}
              y2={padT + innerH}
              stroke="#6366f1"
              strokeWidth={1.5}
              strokeDasharray="4 2"
              opacity={0.6}
            />
          )}

          {/* Sensitivity curve */}
          <path d={pathD} fill="none" stroke="#7c3aed" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />

          {/* Colored dots */}
          {points.map((pt, i) => (
            <circle
              key={pt.delta}
              cx={xScale(i)}
              cy={yScale(pt.probability)}
              r={i === baseIdx ? 5 : 3.5}
              fill={probColor(pt.probability)}
              stroke={i === baseIdx ? "#6366f1" : "white"}
              strokeWidth={i === baseIdx ? 2 : 1}
            />
          ))}

          {/* X-axis labels */}
          {points.map((pt, i) => (
            <text
              key={pt.delta}
              x={xScale(i)}
              y={padT + innerH + 12}
              textAnchor="middle"
              fontSize={8}
              fill={pt.delta === 0 ? "#6366f1" : "#9ca3af"}
              fontWeight={pt.delta === 0 ? "bold" : "normal"}
            >
              {pt.delta > 0 ? `+${pt.delta}` : pt.delta}%
            </text>
          ))}
          <text
            x={padL + innerW / 2}
            y={svgH - 2}
            textAnchor="middle"
            fontSize={8}
            fill="#6b7280"
          >
            Price change from base ({formatValue(basePrice)})
          </text>
        </svg>

        {/* Key data points */}
        <div className="grid grid-cols-3 gap-2">
          {[-10, 0, 10].map((d) => {
            const pt = points.find((p) => p.delta === d);
            if (!pt) return null;
            return (
              <div
                key={d}
                className="text-center p-2 rounded border"
                style={{ borderColor: probColor(pt.probability) + "40", backgroundColor: probColor(pt.probability) + "10" }}
              >
                <p className="text-xs text-muted-foreground">
                  {d === 0 ? "Base" : d > 0 ? `+${d}%` : `${d}%`}
                </p>
                <p className="text-sm font-semibold">{formatValue(pt.price)}</p>
                <p className="text-xs font-bold" style={{ color: probColor(pt.probability) }}>
                  {pt.probability.toFixed(0)}% win
                </p>
              </div>
            );
          })}
        </div>

        <p className="text-xs text-muted-foreground text-center">
          Estimated elasticity: {Math.abs(elasticity).toFixed(1)}pp win probability per 1% price change
        </p>
      </CardContent>
    </Card>
  );
}
