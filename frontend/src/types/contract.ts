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
