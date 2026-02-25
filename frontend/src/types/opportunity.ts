export interface Opportunity {
  id: string;
  notice_id: string;
  title: string;
  description: string;
  agency: string;
  sub_agency: string;
  notice_type: string;
  sol_number: string;
  naics_code: string;
  naics_description: string;
  psc_code: string;
  set_aside: string;
  posted_date: string;
  response_deadline: string;
  estimated_value: number | null;
  place_of_performance: string;
  status: string;
  keywords: string[];
  contacts: Contact[];
  attachments: Attachment[];
  source_url: string;
  score?: OpportunityScore;
  days_until_deadline: number | null;
}

export interface OpportunityScore {
  total_score: number;
  recommendation: "strong_bid" | "bid" | "consider" | "no_bid";
  naics_match: number;
  psc_match: number;
  keyword_overlap: number;
  capability_similarity: number;
  past_performance_relevance: number;
  value_fit: number;
  deadline_feasibility: number;
  set_aside_match: number;
  competition_intensity: number;
  risk_factors: number;
  score_explanation: Record<string, string>;
  ai_rationale: string;
}

export interface Contact {
  name: string;
  email: string;
  phone: string;
  type: string;
}

export interface Attachment {
  name: string;
  url: string;
  size: number | null;
}
