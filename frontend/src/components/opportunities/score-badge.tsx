"use client";

import { cn } from "@/lib/utils";

interface ScoreBadgeProps {
  score: number;
  recommendation: string;
  size?: "sm" | "md" | "lg";
}

const recommendationColors: Record<string, string> = {
  strong_bid: "bg-green-100 text-green-800 border-green-300",
  bid: "bg-blue-100 text-blue-800 border-blue-300",
  consider: "bg-yellow-100 text-yellow-800 border-yellow-300",
  no_bid: "bg-red-100 text-red-800 border-red-300",
};

const recommendationLabels: Record<string, string> = {
  strong_bid: "Strong Bid",
  bid: "Bid",
  consider: "Consider",
  no_bid: "No Bid",
};

const sizeClasses: Record<string, string> = {
  sm: "px-2 py-0.5 text-xs",
  md: "px-2.5 py-1 text-sm",
  lg: "px-3 py-1.5 text-base",
};

export function ScoreBadge({
  score,
  recommendation,
  size = "md",
}: ScoreBadgeProps) {
  const colorClass =
    recommendationColors[recommendation] || recommendationColors.no_bid;
  const sizeClass = sizeClasses[size];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-medium",
        colorClass,
        sizeClass
      )}
    >
      {score}
    </span>
  );
}

export function RecommendationBadge({
  recommendation,
  size = "md",
}: {
  recommendation: string;
  size?: "sm" | "md" | "lg";
}) {
  const colorClass =
    recommendationColors[recommendation] || recommendationColors.no_bid;
  const label =
    recommendationLabels[recommendation] || recommendation;
  const sizeClass = sizeClasses[size];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border font-medium",
        colorClass,
        sizeClass
      )}
    >
      {label}
    </span>
  );
}
