export type ClearanceType = "none" | "confidential" | "secret" | "top_secret" | "ts_sci";
export type ClearanceStatus = "active" | "pending" | "expired" | "not_required";

export interface Employee {
  id: string;
  name: string;
  email: string;
  title: string;
  department: string;
  clearance_type: ClearanceType;
  clearance_type_display?: string;
  clearance_status: ClearanceStatus;
  clearance_status_display?: string;
  clearance_expiry: string | null;
  hire_date: string;
  skills: string[];
  certifications: string[];
  labor_category: string;
  hourly_rate: string | null;
  utilization_target: number;
  is_active: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface SkillMatrix {
  id: string;
  employee: string;
  employee_name?: string;
  skill_name: string;
  proficiency_level: number;
  proficiency_level_display?: string;
  years_experience: number;
  last_assessed_date: string | null;
  verified_by: string;
}

export interface Assignment {
  id: string;
  employee: string;
  employee_name?: string;
  contract: string | null;
  deal: string | null;
  role: string;
  start_date: string;
  end_date: string | null;
  allocation_percentage: number;
  is_active: boolean;
}

export interface HiringRequisition {
  id: string;
  title: string;
  department: string;
  labor_category: string;
  clearance_required: ClearanceType;
  skills_required: string[];
  min_experience_years: number;
  status: "open" | "sourcing" | "interviewing" | "offer" | "filled" | "cancelled";
  status_display?: string;
  priority: number;
  priority_display?: string;
  linked_deal: string | null;
  justification: string;
  target_start_date: string | null;
  filled_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface DemandForecast {
  forecast: Record<string, number>;
  pipeline_deals: number;
  current_capacity: Record<string, number>;
  gaps: Record<string, number>;
  details: Record<string, unknown>[];
}
