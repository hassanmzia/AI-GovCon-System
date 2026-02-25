"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users } from "lucide-react";

interface LaborCategory {
  label: string;
  current: number;  // current headcount
  demand: number;   // pipeline-weighted demand (FTEs)
}

interface WorkforceHeatmapProps {
  categories: LaborCategory[];
}

function gapColor(gap: number): { bg: string; text: string; label: string } {
  if (gap >= 3) return { bg: "#fee2e2", text: "#b91c1c", label: "Critical" };
  if (gap >= 1) return { bg: "#fef3c7", text: "#b45309", label: "Shortage" };
  if (gap >= -1) return { bg: "#d1fae5", text: "#065f46", label: "Balanced" };
  return { bg: "#dbeafe", text: "#1e40af", label: "Surplus" };
}

function utilizationColor(pct: number): string {
  if (pct >= 90) return "#ef4444";
  if (pct >= 75) return "#f59e0b";
  if (pct >= 50) return "#10b981";
  return "#94a3b8";
}

const DEFAULT_CATEGORIES: LaborCategory[] = [
  { label: "Program Manager", current: 4, demand: 5.2 },
  { label: "Systems Engineer", current: 8, demand: 7.5 },
  { label: "Software Engineer", current: 12, demand: 14.8 },
  { label: "Data Scientist", current: 3, demand: 5.0 },
  { label: "Cybersecurity", current: 5, demand: 4.3 },
  { label: "Cloud Architect", current: 2, demand: 3.5 },
  { label: "Business Analyst", current: 6, demand: 5.8 },
  { label: "QA Engineer", current: 4, demand: 3.2 },
];

export function WorkforceHeatmap({ categories }: WorkforceHeatmapProps) {
  const data = categories && categories.length > 0 ? categories : DEFAULT_CATEGORIES;
  const totalCurrent = data.reduce((s, c) => s + c.current, 0);
  const totalDemand = data.reduce((s, c) => s + c.demand, 0);
  const totalGap = totalDemand - totalCurrent;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Users className="h-4 w-4 text-indigo-500" /> Workforce Demand Heatmap
          <span className="ml-auto text-xs font-normal text-muted-foreground">
            {totalCurrent} staff · {totalDemand.toFixed(1)} FTE demand
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {/* Summary row */}
        <div className="grid grid-cols-3 gap-2 mb-3">
          {[
            { label: "Total Staff", value: totalCurrent.toString(), color: "text-foreground" },
            { label: "Pipeline Demand", value: totalDemand.toFixed(1) + " FTE", color: "text-indigo-600" },
            {
              label: "Net Gap",
              value: (totalGap > 0 ? "+" : "") + totalGap.toFixed(1),
              color: totalGap > 2 ? "text-red-600" : totalGap > 0 ? "text-amber-600" : "text-emerald-600",
            },
          ].map((s) => (
            <div key={s.label} className="text-center bg-muted/40 rounded p-2">
              <p className="text-xs text-muted-foreground">{s.label}</p>
              <p className={`text-sm font-bold ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Heatmap rows */}
        <div className="space-y-1.5">
          {data.map((cat) => {
            const gap = cat.demand - cat.current;
            const { bg, text, label } = gapColor(gap);
            const utilizationPct = cat.current > 0 ? (cat.demand / cat.current) * 100 : 100;
            const barPct = Math.min((cat.current / Math.max(cat.demand, cat.current)) * 100, 100);

            return (
              <div
                key={cat.label}
                className="flex items-center gap-2 rounded px-2 py-1.5 text-xs"
                style={{ backgroundColor: bg + "80" }}
              >
                {/* Label */}
                <span className="w-36 font-medium text-foreground truncate">{cat.label}</span>

                {/* Bar: current vs demand */}
                <div className="flex-1 h-4 bg-white/60 rounded overflow-hidden relative">
                  <div
                    className="absolute inset-y-0 left-0 rounded transition-all"
                    style={{
                      width: `${barPct}%`,
                      backgroundColor: utilizationColor(utilizationPct),
                      opacity: 0.75,
                    }}
                  />
                  {/* Demand marker */}
                  <div
                    className="absolute inset-y-0 w-0.5 bg-gray-700"
                    style={{ left: `${Math.min((cat.demand / Math.max(cat.current + 2, cat.demand + 1)) * 100, 99)}%` }}
                  />
                </div>

                {/* Numbers */}
                <div className="flex items-center gap-1.5 w-28 text-right justify-end">
                  <span className="text-muted-foreground">{cat.current} staff</span>
                  <span className="text-muted-foreground">→</span>
                  <span className="font-medium">{cat.demand.toFixed(1)} FTE</span>
                </div>

                {/* Status badge */}
                <span
                  className="w-16 text-center text-[10px] font-semibold rounded px-1 py-0.5"
                  style={{ color: text, backgroundColor: bg }}
                >
                  {gap > 0 ? `+${gap.toFixed(1)}` : gap.toFixed(1)} {label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 pt-2 text-xs text-muted-foreground flex-wrap">
          {[
            { bg: "#fee2e2", text: "#b91c1c", label: "Critical shortage (≥3)" },
            { bg: "#fef3c7", text: "#b45309", label: "Shortage (1–3)" },
            { bg: "#d1fae5", text: "#065f46", label: "Balanced" },
            { bg: "#dbeafe", text: "#1e40af", label: "Surplus" },
          ].map((l) => (
            <div key={l.label} className="flex items-center gap-1">
              <div className="w-3 h-3 rounded border" style={{ backgroundColor: l.bg, borderColor: l.text + "40" }} />
              <span style={{ color: l.text }}>{l.label}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">Demand = pipeline-weighted FTE need · Bar = current / demand ratio</p>
      </CardContent>
    </Card>
  );
}
