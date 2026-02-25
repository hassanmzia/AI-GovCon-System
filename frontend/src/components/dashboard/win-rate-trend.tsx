"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp } from "lucide-react";

interface WinLossRecord {
  outcome: "won" | "lost" | "no_bid";
  created_at: string;
}

interface WinRateTrendProps {
  records: WinLossRecord[];
  currentWinRate: number | null;
}

function groupByMonth(records: WinLossRecord[]): Array<{ label: string; wins: number; losses: number; rate: number }> {
  const now = new Date();
  const months: Array<{ label: string; wins: number; losses: number; rate: number }> = [];

  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const label = d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
    const monthRecords = records.filter((r) => {
      const rd = new Date(r.created_at);
      return rd.getFullYear() === d.getFullYear() && rd.getMonth() === d.getMonth();
    });
    const wins = monthRecords.filter((r) => r.outcome === "won").length;
    const losses = monthRecords.filter((r) => r.outcome === "lost").length;
    const total = wins + losses;
    months.push({ label, wins, losses, rate: total > 0 ? (wins / total) * 100 : 0 });
  }
  return months;
}

export function WinRateTrend({ records, currentWinRate }: WinRateTrendProps) {
  const months = groupByMonth(records);
  const hasData = months.some((m) => m.wins + m.losses > 0);
  const svgWidth = 360;
  const svgHeight = 100;
  const padL = 30;
  const padR = 10;
  const padT = 10;
  const padB = 20;
  const w = svgWidth - padL - padR;
  const h = svgHeight - padT - padB;
  const n = months.length;

  const xScale = (i: number) => padL + (i / (n - 1)) * w;
  const yScale = (r: number) => padT + h - (r / 100) * h;

  const pathPoints = months
    .map((m, i) => ({ x: xScale(i), y: yScale(m.rate), valid: m.wins + m.losses > 0 }));

  const validPoints = pathPoints.filter((p) => p.valid);

  let pathD = "";
  if (validPoints.length > 1) {
    pathD = validPoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  }

  const displayRate = currentWinRate != null ? currentWinRate : (hasData ? months[months.length - 1].rate : null);
  const trend = hasData && months.length >= 2
    ? months[months.length - 1].rate - months[months.length - 2].rate
    : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-emerald-500" /> Win Rate Trend
          {displayRate != null && (
            <span className={`ml-auto text-lg font-bold ${displayRate >= 50 ? "text-emerald-600" : displayRate >= 30 ? "text-yellow-600" : "text-red-600"}`}>
              {displayRate.toFixed(0)}%
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            No win/loss data in the last 6 months
          </div>
        ) : (
          <div className="space-y-2">
            <svg width="100%" viewBox={`0 0 ${svgWidth} ${svgHeight}`} preserveAspectRatio="xMidYMid meet">
              {/* Grid */}
              {[0, 25, 50, 75, 100].map((r) => (
                <g key={r}>
                  <line x1={padL} y1={yScale(r)} x2={padL + w} y2={yScale(r)} stroke="#e5e7eb" strokeWidth={1} />
                  <text x={padL - 4} y={yScale(r) + 3} textAnchor="end" fontSize={8} fill="#9ca3af">{r}%</text>
                </g>
              ))}
              {/* 50% reference line */}
              <line x1={padL} y1={yScale(50)} x2={padL + w} y2={yScale(50)} stroke="#d1d5db" strokeWidth={1.5} strokeDasharray="4 2" />

              {/* Trend line */}
              {pathD && <path d={pathD} fill="none" stroke="#10b981" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />}

              {/* Data points */}
              {pathPoints.map((p, i) => p.valid && (
                <circle key={i} cx={p.x} cy={p.y} r={4} fill="#10b981" />
              ))}

              {/* X labels */}
              {months.map((m, i) => (
                <text key={m.label} x={xScale(i)} y={svgHeight - 4} textAnchor="middle" fontSize={8} fill="#9ca3af">
                  {m.label}
                </text>
              ))}
            </svg>

            {/* Monthly summary */}
            <div className="grid grid-cols-6 gap-1 text-center text-xs pt-1">
              {months.map((m) => (
                <div key={m.label}>
                  {m.wins + m.losses > 0 ? (
                    <div className="flex justify-center gap-0.5">
                      <span className="text-emerald-600 font-medium">{m.wins}W</span>
                      <span className="text-gray-300">/</span>
                      <span className="text-red-500">{m.losses}L</span>
                    </div>
                  ) : (
                    <span className="text-muted-foreground">--</span>
                  )}
                </div>
              ))}
            </div>

            {trend != null && Math.abs(trend) >= 1 && (
              <p className={`text-xs text-center ${trend > 0 ? "text-emerald-600" : "text-red-600"}`}>
                {trend > 0 ? "▲" : "▼"} {Math.abs(trend).toFixed(0)}pp vs prior month
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
