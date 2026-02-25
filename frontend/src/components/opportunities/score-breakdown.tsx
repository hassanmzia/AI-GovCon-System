"use client";

import { OpportunityScore } from "@/types/opportunity";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScoreBadge, RecommendationBadge } from "./score-badge";
import { cn } from "@/lib/utils";

interface ScoreBreakdownProps {
  score: OpportunityScore;
}

const factorLabels: Record<string, string> = {
  naics_match: "NAICS Match",
  psc_match: "PSC Match",
  keyword_overlap: "Keyword Overlap",
  capability_similarity: "Capability Similarity",
  past_performance_relevance: "Past Performance",
  value_fit: "Value Fit",
  deadline_feasibility: "Deadline Feasibility",
  set_aside_match: "Set-Aside Match",
  competition_intensity: "Competition Intensity",
  risk_factors: "Risk Factors",
};

function getBarColor(value: number): string {
  if (value < 30) return "bg-red-500";
  if (value <= 60) return "bg-yellow-500";
  return "bg-green-500";
}

function getTotalScoreColor(recommendation: string): string {
  switch (recommendation) {
    case "strong_bid":
      return "text-green-600";
    case "bid":
      return "text-blue-600";
    case "consider":
      return "text-yellow-600";
    case "no_bid":
      return "text-red-600";
    default:
      return "text-muted-foreground";
  }
}

export function ScoreBreakdown({ score }: ScoreBreakdownProps) {
  const factors = [
    { key: "naics_match", value: score.naics_match },
    { key: "psc_match", value: score.psc_match },
    { key: "keyword_overlap", value: score.keyword_overlap },
    { key: "capability_similarity", value: score.capability_similarity },
    { key: "past_performance_relevance", value: score.past_performance_relevance },
    { key: "value_fit", value: score.value_fit },
    { key: "deadline_feasibility", value: score.deadline_feasibility },
    { key: "set_aside_match", value: score.set_aside_match },
    { key: "competition_intensity", value: score.competition_intensity },
    { key: "risk_factors", value: score.risk_factors },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Score Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Total Score */}
        <div className="flex flex-col items-center gap-2 pb-4 border-b">
          <span
            className={cn(
              "text-5xl font-bold",
              getTotalScoreColor(score.recommendation)
            )}
          >
            {score.total_score}
          </span>
          <RecommendationBadge
            recommendation={score.recommendation}
            size="lg"
          />
        </div>

        {/* Factor Bars */}
        <div className="space-y-3">
          {factors.map(({ key, value }) => (
            <div key={key} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  {factorLabels[key] || key}
                </span>
                <span className="font-medium">{value}</span>
              </div>
              <div className="h-2 w-full rounded-full bg-secondary">
                <div
                  className={cn(
                    "h-2 rounded-full transition-all",
                    getBarColor(value)
                  )}
                  style={{ width: `${Math.min(value, 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* AI Rationale */}
        {score.ai_rationale && (
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium mb-2">AI Rationale</h4>
            <p className="text-sm italic text-muted-foreground leading-relaxed">
              {score.ai_rationale}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
