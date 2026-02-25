export type PerformanceRating =
  | "Exceptional"
  | "Very Good"
  | "Satisfactory"
  | "Marginal"
  | "Unsatisfactory"
  | "";

export type ContractType = "FFP" | "T&M" | "CPFF" | "CPAF" | "IDIQ" | "BPA" | "";

export interface PastPerformance {
  id: string;
  project_name: string;
  contract_number: string;
  client_agency: string;
  client_name: string;
  client_email: string;
  client_phone: string;
  description: string;
  relevance_keywords: string[];
  naics_codes: string[];
  technologies: string[];
  domains: string[];
  start_date: string | null;
  end_date: string | null;
  contract_value: string | null;
  contract_type: ContractType;
  performance_rating: PerformanceRating;
  cpars_rating: string;
  on_time_delivery: boolean;
  within_budget: boolean;
  key_achievements: string[];
  metrics: Record<string, string | number>;
  narrative: string;
  lessons_learned: string;
  is_active: boolean;
  last_verified: string | null;
  created_at: string;
  updated_at: string;
}

export interface PastPerformanceMatch {
  id: string;
  opportunity: string;
  past_performance: PastPerformance;
  relevance_score: number;
  match_rationale: string;
  matched_keywords: string[];
}

export interface CreatePastPerformancePayload {
  project_name: string;
  contract_number?: string;
  client_agency: string;
  client_name?: string;
  description: string;
  relevance_keywords?: string[];
  naics_codes?: string[];
  technologies?: string[];
  domains?: string[];
  start_date?: string;
  end_date?: string;
  contract_value?: string;
  contract_type?: ContractType;
  performance_rating?: PerformanceRating;
  cpars_rating?: string;
  on_time_delivery?: boolean;
  within_budget?: boolean;
  key_achievements?: string[];
  metrics?: Record<string, string | number>;
  narrative?: string;
  lessons_learned?: string;
}
