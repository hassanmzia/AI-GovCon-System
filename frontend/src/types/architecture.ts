// Output of the Solution Architect Agent (SolutionArchitectState)

export interface ArchitectureDiagram {
  title: string;
  type: string;       // "System Context", "Container", "Data Flow", etc.
  mermaid: string;    // Raw Mermaid.js code
  description: string;
}

export interface RequirementAnalysis {
  functional?: string;
  non_functional?: string;
  security?: string;
  integration?: string;
  data?: string;
  ai_ml?: string;
  infrastructure?: string;
  design_decisions?: string;
  risk_flags?: string;
  complexity?: string;
  [key: string]: string | undefined;
}

export interface TechnicalSolution {
  // 17 architecture areas returned by the agent
  executive_summary?: string;
  architecture_pattern?: string;
  core_components?: string;
  integration_approach?: string;
  data_architecture?: string;
  security_architecture?: string;
  infrastructure?: string;
  ai_ml_components?: string;
  devops_cicd?: string;
  monitoring_observability?: string;
  disaster_recovery?: string;
  scalability?: string;
  compliance_implementation?: string;
  innovation_differentiators?: string;
  risk_mitigation?: string;
  loe_estimates?: string;
  technology_stack?: string;
  [key: string]: string | undefined;
}

export interface TechnicalVolume {
  sections: Record<string, string>;  // section title → full text
  diagram_count: number;
  word_count?: number;
}

export interface ValidationReport {
  overall_quality: "excellent" | "good" | "needs_revision" | string;
  issues: string[];
  suggestions: string[];
  compliance_gaps: string[];
  score?: number;   // 0-100
  pass?: boolean;
}

export interface ArchitectureResult {
  deal_id: string;
  opportunity_id: string;
  selected_frameworks: string[];
  requirement_analysis: RequirementAnalysis;
  technical_solution: TechnicalSolution;
  diagrams: ArchitectureDiagram[];
  technical_volume: TechnicalVolume;
  validation_report: ValidationReport;
  iteration_count: number;
}
