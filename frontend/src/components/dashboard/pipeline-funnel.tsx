"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Filter } from "lucide-react";
import { DealStage } from "@/types/deal";

interface StageCount {
  stage: DealStage;
  count: number;
}

const STAGE_LABELS: Partial<Record<DealStage, string>> = {
  intake: "Intake",
  qualify: "Qualify",
  bid_no_bid: "Bid/No-Bid",
  capture_plan: "Capture",
  proposal_dev: "Proposal Dev",
  red_team: "Red Team",
  final_review: "Final Review",
  submit: "Submit",
  award_pending: "Award Pending",
  contract_setup: "Contract",
  delivery: "Delivery",
};

const STAGE_COLORS: Partial<Record<DealStage, string>> = {
  intake: "bg-slate-400",
  qualify: "bg-blue-400",
  bid_no_bid: "bg-yellow-400",
  capture_plan: "bg-orange-400",
  proposal_dev: "bg-purple-500",
  red_team: "bg-red-400",
  final_review: "bg-orange-500",
  submit: "bg-green-400",
  award_pending: "bg-yellow-500",
  contract_setup: "bg-blue-600",
  delivery: "bg-emerald-500",
};

const FUNNEL_ORDER: DealStage[] = [
  "intake",
  "qualify",
  "bid_no_bid",
  "capture_plan",
  "proposal_dev",
  "red_team",
  "final_review",
  "submit",
  "award_pending",
  "contract_setup",
  "delivery",
];

interface PipelineFunnelProps {
  distribution: StageCount[];
}

export function PipelineFunnel({ distribution }: PipelineFunnelProps) {
  const stageMap = new Map(distribution.map((d) => [d.stage, d.count]));
  const funnelStages = FUNNEL_ORDER.filter((s) => (stageMap.get(s) || 0) > 0 || true).slice(0, 8);
  const maxCount = Math.max(...funnelStages.map((s) => stageMap.get(s) || 0), 1);
  const totalActive = distribution.reduce((sum, d) => sum + d.count, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Filter className="h-4 w-4 text-blue-500" /> Pipeline Funnel
          {totalActive > 0 && (
            <span className="text-xs font-normal text-muted-foreground ml-1">
              {totalActive} total deals
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {totalActive === 0 ? (
          <div className="flex items-center justify-center h-20 text-muted-foreground text-sm">
            No active deals in pipeline
          </div>
        ) : (
          <div className="space-y-2">
            {funnelStages.map((stage) => {
              const count = stageMap.get(stage) || 0;
              const pct = (count / maxCount) * 100;
              const color = STAGE_COLORS[stage] || "bg-gray-300";
              const label = STAGE_LABELS[stage] || stage;

              return (
                <div key={stage} className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground w-24 text-right">{label}</span>
                  <div className="flex-1 h-6 bg-gray-100 rounded overflow-hidden">
                    <div
                      className={`h-full ${color} rounded transition-all flex items-center pl-2`}
                      style={{ width: `${Math.max(pct, count > 0 ? 8 : 0)}%` }}
                    >
                      {count > 0 && (
                        <span className="text-white text-xs font-bold">{count}</span>
                      )}
                    </div>
                  </div>
                  <span className="text-xs font-medium w-6 text-right text-muted-foreground">
                    {count || ""}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
