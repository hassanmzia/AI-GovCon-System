export type DealStage =
  | "intake"
  | "qualify"
  | "bid_no_bid"
  | "capture_plan"
  | "proposal_dev"
  | "red_team"
  | "final_review"
  | "submit"
  | "post_submit"
  | "award_pending"
  | "contract_setup"
  | "delivery"
  | "closed_won"
  | "closed_lost"
  | "no_bid";

export type DealOutcome = "won" | "lost" | "no_bid" | "cancelled" | "";

export type DealPriority = 1 | 2 | 3 | 4;

export interface Deal {
  id: string;
  title: string;
  stage: DealStage;
  stage_display: string;
  priority: DealPriority;
  priority_display: "Critical" | "High" | "Medium" | "Low";
  estimated_value: string | null;
  win_probability: number;
  composite_score: number;
  owner: string;
  owner_name: string;
  opportunity: string;
  opportunity_title: string;
  due_date: string | null;
  outcome: DealOutcome;
  task_count: number;
  pending_approval_count: number;
  created_at: string;
  updated_at: string;
}

export interface DealListResponse {
  results: Deal[];
  count: number;
}

export interface DealStageHistory {
  id: string;
  from_stage: DealStage | null;
  to_stage: DealStage;
  transitioned_at: string;
  transitioned_by_name: string;
  reason: string;
}

export interface DealTask {
  id: string;
  deal: string;
  title: string;
  description: string;
  stage: DealStage;
  status: "pending" | "in_progress" | "completed" | "skipped";
  due_date: string | null;
  completed_at: string | null;
  assigned_to_name: string | null;
}

export interface DealApproval {
  id: string;
  deal: string;
  stage: DealStage;
  status: "pending" | "approved" | "rejected";
  requested_by_name: string;
  decided_by_name: string | null;
  decision_rationale: string;
  requested_at: string;
  decided_at: string | null;
}

export interface DealPipelineSummary {
  stage: DealStage;
  stage_display: string;
  count: number;
  total_value: number;
  avg_win_probability: number;
}

export interface CreateDealPayload {
  title: string;
  opportunity: string;
  priority?: DealPriority;
  estimated_value?: string;
  due_date?: string;
}

export interface TransitionStagePayload {
  target_stage: DealStage;
  reason?: string;
}

export interface ApprovalDecisionPayload {
  status: "approved" | "rejected";
  decision_rationale: string;
}
