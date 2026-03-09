export type ContractType =
  | "FFP"
  | "T&M"
  | "CPFF"
  | "CPAF"
  | "CPIF"
  | "IDIQ"
  | "BPA";

export type ContractStatus =
  | "drafting"
  | "review"
  | "negotiation"
  | "pending_execution"
  | "executed"
  | "active"
  | "modification"
  | "closeout"
  | "terminated"
  | "expired";

export interface Contract {
  id: string;
  deal: string;
  deal_name?: string;
  contract_number: string;
  title: string;
  contract_type: ContractType;
  status: ContractStatus;
  total_value: number | null;
  period_of_performance_start: string | null;
  period_of_performance_end: string | null;
  option_years: number;
  contracting_officer: string;
  contracting_officer_email: string;
  cor_name: string;
  awarded_date: string | null;
  executed_date: string | null;
  notes: string;
  created_at: string;
}

export interface ContractTemplate {
  id: string;
  name: string;
  contract_type: ContractType;
  description: string;
  sections: Record<string, string>;
  version: string;
  is_active: boolean;
  created_at: string;
}

export interface ContractClause {
  id: string;
  clause_number: string;
  title: string;
  clause_type:
    | "standard"
    | "special"
    | "custom"
    | "far_reference"
    | "dfars_reference";
  clause_text?: string;
  text?: string;
  source?: string;
  category: string;
  is_negotiable: boolean;
  is_mandatory?: boolean;
  risk_level: "low" | "medium" | "high";
  applicability?: string;
  notes: string;
  created_at?: string;
}

export interface ContractVersion {
  id: string;
  contract: string;
  version_number: number;
  change_type:
    | "initial"
    | "modification"
    | "amendment"
    | "option_exercise"
    | "administrative";
  description: string;
  effective_date: string | null;
  created_at: string;
}

export type MilestoneType =
  | "deliverable"
  | "payment"
  | "review"
  | "option"
  | "transition"
  | "closeout";

export type MilestoneStatus =
  | "upcoming"
  | "in_progress"
  | "completed"
  | "overdue"
  | "waived";

export interface ContractMilestone {
  id: string;
  contract: string;
  title: string;
  milestone_type: MilestoneType;
  milestone_type_display: string;
  due_date: string;
  status: MilestoneStatus;
  status_display: string;
  completed_date: string | null;
  amount: number | null;
  deliverable_description: string;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
}

export type ModificationType =
  | "bilateral"
  | "unilateral"
  | "administrative"
  | "funding"
  | "scope"
  | "period_extension";

export type ModificationStatus =
  | "proposed"
  | "reviewing"
  | "approved"
  | "executed"
  | "rejected";

export interface ContractModification {
  id: string;
  contract: string;
  modification_number: string;
  modification_type: ModificationType;
  modification_type_display: string;
  description: string;
  impact_value: number | null;
  new_total_value: number | null;
  effective_date: string | null;
  status: ModificationStatus;
  status_display: string;
  requested_by: string | null;
  approved_by: string | null;
  created_at: string;
  updated_at: string;
}

export type OptionYearStatus = "pending" | "exercised" | "declined" | "expired";

export interface OptionYear {
  id: string;
  contract: string;
  year_number: number;
  start_date: string;
  end_date: string;
  value: number;
  status: OptionYearStatus;
  status_display: string;
  exercised_date: string | null;
  decision_deadline: string;
  created_at: string;
  updated_at: string;
}
