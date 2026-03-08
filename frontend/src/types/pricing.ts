export interface RateCardRate {
  labor_category: string;
  level: string;
  hourly_rate: number;
  indirect_rate: number;
  escalation_rate: number;
}

export interface RateCard {
  id: string;
  name: string;
  fiscal_year: string;
  is_active: boolean;
  rates: RateCardRate[];
  created_at: string;
}

export interface PricingScenario {
  id: string;
  deal: string;
  cost_model?: string | null;
  name: string;
  strategy_type: "max_profit" | "value_based" | "competitive" | "aggressive" | "incumbent_match" | "budget_fit" | "floor";
  strategy_type_display?: string;
  total_price: number;
  profit: number;
  margin_pct: number;
  probability_of_win: number;
  expected_value: number;
  competitive_position: string;
  sensitivity_data: Record<string, unknown>;
  is_recommended: boolean;
  rationale: string;
  created_at: string;
  updated_at: string;
}

export interface LOEEstimate {
  id: string;
  scenario: string;
  labor_category: string;
  level: string;
  hours_per_month: number;
  months: number;
  total_hours: number;
  hourly_rate: number;
  total_cost: number;
}

export interface CostModel {
  id: string;
  deal: string;
  version: number;
  direct_labor: number;
  fringe_benefits: number;
  overhead: number;
  odcs: number;
  subcontractor_costs: number;
  travel: number;
  materials: number;
  ga_expense: number;
  total_cost: number;
  fringe_rate: number;
  overhead_rate: number;
  ga_rate: number;
  created_at: string;
}

export interface PricingApproval {
  id: string;
  scenario: string;
  status: "pending" | "approved" | "rejected";
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
}
