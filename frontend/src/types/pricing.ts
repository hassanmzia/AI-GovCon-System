/* ── Rate Card ───────────────────────────────────────── */
export interface RateCard {
  id: string;
  labor_category: string;
  gsa_equivalent: string;
  gsa_sin: string;
  internal_rate: string | number;
  gsa_rate: string | number | null;
  proposed_rate: string | number;
  market_low: string | number | null;
  market_median: string | number | null;
  market_high: string | number | null;
  education_requirement: string;
  experience_years: number;
  clearance_required: boolean;
  is_active: boolean;
  effective_date: string | null;
  created_at: string;
  updated_at: string;
}

/* ── Pricing Scenario ───────────────────────────────── */
export interface PricingScenario {
  id: string;
  deal: string;
  cost_model?: string | null;
  name: string;
  strategy_type: "max_profit" | "value_based" | "competitive" | "aggressive" | "incumbent_match" | "budget_fit" | "floor";
  strategy_type_display?: string;
  total_price: string | number;
  profit: string | number;
  margin_pct: number;
  probability_of_win: number;
  expected_value: string | number;
  competitive_position: string;
  sensitivity_data: Record<string, unknown>;
  is_recommended: boolean;
  rationale: string;
  created_at: string;
  updated_at: string;
}

/* ── WBS Element (inside LOEEstimate.wbs_elements) ──── */
export interface WBSElement {
  wbs_id: string;
  name: string;
  labor_category: string;
  hours_optimistic?: number;
  hours_likely?: number;
  hours_pessimistic?: number;
  hours_estimated: number;
}

/* ── LOE Estimate ───────────────────────────────────── */
export interface LOEEstimate {
  id: string;
  deal: string;
  version: number;
  wbs_elements: WBSElement[];
  total_hours: number;
  total_ftes: number;
  duration_months: number;
  staffing_plan: Record<string, Record<string, number>>;
  key_personnel: Array<Record<string, unknown>>;
  estimation_method: string;
  estimation_method_display?: string;
  confidence_level: number;
  assumptions: string[];
  risks: string[];
  created_at: string;
  updated_at: string;
}

/* ── Cost Model ─────────────────────────────────────── */
export interface CostModel {
  id: string;
  deal: string;
  loe: string | null;
  version: number;
  direct_labor: string | number;
  fringe_benefits: string | number;
  overhead: string | number;
  odcs: string | number;
  subcontractor_costs: string | number;
  travel: string | number;
  materials: string | number;
  ga_expense: string | number;
  total_cost: string | number;
  fringe_rate: number;
  overhead_rate: number;
  ga_rate: number;
  labor_detail: Array<{ category: string; hours: number; rate: number; total: number }>;
  odc_detail: Array<Record<string, unknown>>;
  travel_detail: Array<Record<string, unknown>>;
  sub_detail: Array<Record<string, unknown>>;
  created_at: string;
}

/* ── Pricing Approval ───────────────────────────────── */
export interface PricingApproval {
  id: string;
  deal: string;
  scenario: string;
  requested_by: string;
  approved_by: string | null;
  status: "pending" | "approved" | "rejected";
  notes: string;
  decided_at: string | null;
  created_at: string;
  updated_at: string;
}
