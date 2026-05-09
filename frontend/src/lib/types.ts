// Domain types mirroring the backend Pydantic models.
// Keep in sync with backend/models/*.py.

export type Regulation =
  | "gdpr_dsgvo" | "lksg" | "enefg" | "csrd" | "bdsg"
  | "nis2" | "eu_ai_act" | "hinschg" | "arbschg" | "agg" | "milog";
export type Industry =
  | "it_software" | "manufacturing" | "healthcare" | "retail"
  | "finance" | "logistics" | "construction" | "energy"
  | "food_beverage" | "consulting" | "other";
export type ObligationType = "MUST" | "SHOULD" | "MAY";
export type ComplianceStatus = "COMPLIANT" | "PARTIALLY_COMPLIANT" | "NON_COMPLIANT" | "CANNOT_ASSESS";
export type Priority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type AnalysisStep =
  | "profile_validation" | "applicability_determination" | "article_retrieval"
  | "gap_analysis" | "action_plan" | "report_assembly";
export type JobStatus = "pending" | "running" | "completed" | "failed" | "partial";

export interface CompanyProfile {
  company_name: string;
  industry: Industry;
  country?: string;
  employee_count: number;
  annual_revenue_eur?: number;
  balance_sheet_total_eur?: number;
  processes_personal_data: boolean;
  processes_special_category_data?: boolean;
  processing_is_occasional?: boolean;
  has_dpo?: boolean;
  has_processing_records?: boolean;
  has_supply_chain_abroad?: boolean;
  supply_chain_countries?: string[];
  annual_energy_consumption_mwh?: number;
  has_energy_management_system?: boolean;
  has_conducted_energy_audit?: boolean;
  is_listed_company?: boolean;
  has_sustainability_report?: boolean;
  is_critical_infrastructure_sector?: boolean;
  uses_ai_systems?: boolean;
  existing_compliance_notes?: string;
}

export interface RegulationApplicability {
  regulation: Regulation;
  applies: boolean;
  reason: string;
  key_threshold?: string;
}

export interface ComplianceGap {
  regulation: Regulation;
  article_number: string;
  article_title: string;
  status: ComplianceStatus;
  evidence: string;
  deficiency_description?: string;
}

export interface ActionItem {
  regulation: Regulation;
  article_number: string;
  action: string;
  priority: Priority;
  estimated_effort: string;
  deadline?: string;
  dependencies: string[];
  gap_reference: string;
}

export interface RegulationScore {
  regulation: Regulation;
  total_requirements: number;
  compliant: number;
  partially_compliant: number;
  non_compliant: number;
  cannot_assess: number;
  score_percent: number;
}

export interface ComplianceReport {
  job_id: string;
  company_name: string;
  generated_at: string;
  applicable_regulations: RegulationApplicability[];
  inferred_characteristics: string[];
  missing_optional_fields: string[];
  validation_warnings: string[];
  gap_analysis: ComplianceGap[];
  action_plan: ActionItem[];
  regulation_scores: RegulationScore[];
  overall_score_percent: number;
  executive_summary: string;
  disclaimer: string;
  requires_manual_review: string[];
}

export interface StepProgress {
  step: AnalysisStep;
  status: JobStatus;
  message?: string;
  duration_seconds?: number;
}

export interface StatusResponse {
  job_id: string;
  status: JobStatus;
  current_step?: AnalysisStep;
  steps: StepProgress[];
  error?: string;
}

export interface AnalyzeResponse {
  job_id: string;
  status: JobStatus;
  message: string;
}
