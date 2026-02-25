export type PolicyType =
  | "bid_threshold"
  | "approval_gate"
  | "risk_limit"
  | "compliance_requirement"
  | "teaming_rule"
  | "pricing_constraint";

export type PolicyScope = "global" | "deal_type" | "naics_code" | "agency";

export type EvaluationOutcome = "pass" | "warn" | "fail" | "skip";

export type ExceptionStatus = "pending" | "approved" | "rejected";

export interface PolicyRule {
  id: string;
  policy: string;
  rule_name: string;
  field_path: string;
  operator: string;
  threshold_value: string;
  threshold_json: unknown;
  error_message: string;
  warning_message: string;
  is_blocking: boolean;
  created_at: string;
  updated_at: string;
}

export interface BusinessPolicy {
  id: string;
  name: string;
  description: string;
  policy_type: PolicyType;
  scope: PolicyScope;
  conditions: Record<string, unknown>;
  actions: Record<string, unknown>;
  is_active: boolean;
  priority: number;
  effective_date: string | null;
  expiry_date: string | null;
  version: number;
  created_by: string | null;
  created_by_username: string | null;
  rules: PolicyRule[];
  created_at: string;
  updated_at: string;
}

export interface PolicyEvaluation {
  id: string;
  policy: string;
  policy_name: string | null;
  deal: string;
  deal_title: string | null;
  evaluated_at: string;
  outcome: EvaluationOutcome;
  triggered_rules: Record<string, unknown>[];
  recommendations: string[];
  auto_resolved: boolean;
  resolved_by: string | null;
  resolved_by_username: string | null;
  created_at: string;
}

export interface PolicyException {
  id: string;
  policy: string;
  policy_name: string | null;
  deal: string;
  deal_title: string | null;
  reason: string;
  approved_by: string | null;
  approved_by_username: string | null;
  approved_at: string | null;
  expires_at: string | null;
  status: ExceptionStatus;
  requested_by: string | null;
  requested_by_username: string | null;
  created_at: string;
  updated_at: string;
}
