"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp } from "lucide-react";

interface RevenueForecastProps {
  pipelineValue: number;
  winRate: number | null;
  activeDeals: number;
}

interface QuarterForecast {
  label: string;
  low: number;
  mid: number;
  high: number;
}

function formatValue(v: number): string {
  if (v >= 1_000_000_000) return `$${(v / 1_000_000_000).toFixed(1)}B`;
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

function buildForecast(pipelineValue: number, winRate: number): QuarterForecast[] {
  const now = new Date();
  const q = Math.floor(now.getMonth() / 3) + 1;
  const y = now.getFullYear();

  const quarters: QuarterForecast[] = [];
  const quarterValues = [0.25, 0.30, 0.25, 0.20]; // distribution of pipeline across quarters

  for (let i = 0; i < 4; i++) {
    const qi = ((q - 1 + i) % 4) + 1;
    const yi = y + Math.floor((q - 1 + i) / 4);
    const portion = pipelineValue * quarterValues[i];
    const mid = portion * (winRate / 100);
    quarters.push({
      label: `Q${qi} ${yi}`,
      low: mid * 0.7,
      mid,
      high: mid * 1.35,
    });
  }
  return quarters;
}

export function RevenueForecast({ pipelineValue, winRate, activeDeals }: RevenueForecastProps) {
  const effectiveWinRate = winRate ?? 30;
  const quarters = buildForecast(pipelineValue, effectiveWinRate);
  const maxVal = Math.max(...quarters.map((q) => q.high));

  const totalMid = quarters.reduce((s, q) => s + q.mid, 0);
  const totalLow = quarters.reduce((s, q) => s + q.low, 0);
  const totalHigh = quarters.reduce((s, q) => s + q.high, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-green-500" /> 4-Quarter Revenue Forecast
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Bar chart */}
          <div className="flex items-end gap-3 h-32">
            {quarters.map((q) => (
              <div key={q.label} className="flex-1 flex flex-col items-center gap-1">
                <div className="w-full relative flex items-end justify-center" style={{ height: "100px" }}>
                  {/* High */}
                  <div
                    className="absolute bottom-0 w-full bg-green-100 rounded-t"
                    style={{ height: `${(q.high / maxVal) * 100}%` }}
                  />
                  {/* Mid */}
                  <div
                    className="absolute bottom-0 w-3/5 mx-auto bg-green-500 rounded-t"
                    style={{ height: `${(q.mid / maxVal) * 100}%`, left: "20%", right: "20%" }}
                  />
                  {/* Low marker */}
                  <div
                    className="absolute w-full border-t-2 border-dashed border-green-300"
                    style={{ bottom: `${(q.low / maxVal) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground font-medium">{q.label}</span>
                <span className="text-xs font-bold text-green-700">{formatValue(q.mid)}</span>
              </div>
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <div className="w-8 h-3 bg-green-500 rounded" />
              Base ({effectiveWinRate.toFixed(0)}% win rate)
            </div>
            <div className="flex items-center gap-1">
              <div className="w-8 h-3 bg-green-100 rounded border border-green-200" />
              Optimistic
            </div>
          </div>

          {/* Summary */}
          <div className="grid grid-cols-3 gap-3 pt-2 border-t">
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Conservative</p>
              <p className="font-semibold text-sm">{formatValue(totalLow)}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Base</p>
              <p className="font-bold text-green-700">{formatValue(totalMid)}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Optimistic</p>
              <p className="font-semibold text-sm">{formatValue(totalHigh)}</p>
            </div>
          </div>

          <p className="text-xs text-muted-foreground text-center">
            Based on {activeDeals} active deals ({formatValue(pipelineValue)} pipeline)
            {winRate == null && " · using default 30% win rate"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
