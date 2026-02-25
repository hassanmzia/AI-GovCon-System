"use client";

import React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: number; // positive = up, negative = down, 0 = flat
  trendLabel?: string;
  icon?: React.ReactNode;
  className?: string;
  loading?: boolean;
}

export function StatCard({
  title,
  value,
  subtitle,
  trend,
  trendLabel,
  icon,
  className = "",
  loading = false,
}: StatCardProps) {
  const trendDir = trend == null ? null : trend > 0 ? "up" : trend < 0 ? "down" : "flat";

  if (loading) {
    return (
      <div className={cn("rounded-lg border bg-card p-5 space-y-3", className)}>
        <div className="h-4 w-24 bg-muted animate-pulse rounded" />
        <div className="h-8 w-32 bg-muted animate-pulse rounded" />
        <div className="h-3 w-20 bg-muted animate-pulse rounded" />
      </div>
    );
  }

  return (
    <div className={cn("rounded-lg border bg-card p-5", className)}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </div>

      <p className="mt-2 text-2xl font-bold tracking-tight">{value}</p>

      {(subtitle || trendDir != null) && (
        <div className="mt-1 flex items-center gap-2">
          {trendDir != null && (
            <span
              className={cn(
                "inline-flex items-center gap-0.5 text-xs font-medium",
                trendDir === "up" && "text-green-600",
                trendDir === "down" && "text-red-600",
                trendDir === "flat" && "text-muted-foreground"
              )}
            >
              {trendDir === "up" && <TrendingUp className="h-3 w-3" />}
              {trendDir === "down" && <TrendingDown className="h-3 w-3" />}
              {trendDir === "flat" && <Minus className="h-3 w-3" />}
              {trend != null && `${trend > 0 ? "+" : ""}${trend}%`}
            </span>
          )}
          {subtitle && <span className="text-xs text-muted-foreground">{subtitle}</span>}
          {trendLabel && <span className="text-xs text-muted-foreground">{trendLabel}</span>}
        </div>
      )}
    </div>
  );
}
