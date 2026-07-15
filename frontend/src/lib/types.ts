// Domain types mirroring the backend Pydantic models.
// Keep in sync with backend/models/*.py.

export type Regulation =
  | "gdpr_dsgvo" | "lksg" | "enefg" | "csrd" | "bdsg"
  | "nis2" | "eu_ai_act" | "hinschg" | "workplace_law" | "arbschg" | "agg" | "milog"
  | "ttdsg" | "gwg" | "eu_data_act";
export type Industry =
  | "it_software" | "manufacturing" | "healthcare" | "retail"
  | "finance" | "logistics" | "construction" | "energy"
  | "food_beverage" | "consulting" | "real_estate" | "chemicals"
  | "transport" | "water" | "digital" | "government" | "space"
  | "waste" | "research" | "gambling" | "crypto" | "other";
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
  // GDPR / BDSG policies
  has_privacy_policy?: boolean;
  has_processor_agreements?: boolean;
  has_data_breach_procedure?: boolean;
  has_tom_documentation?: boolean;
  has_data_retention_policy?: boolean;
  has_data_protection_training?: boolean;
  transfers_data_outside_eea?: boolean;
  has_consent_management?: boolean;
  // NIS2
  has_information_security_policy?: boolean;
  has_incident_response_plan?: boolean;
  has_business_continuity_plan?: boolean;
  has_vulnerability_management?: boolean;
  has_mfa_implemented?: boolean;
  has_supply_chain_security_assessment?: boolean;
  has_security_awareness_training?: boolean;
  // EU AI Act
  ai_systems_are_high_risk?: boolean;
  has_ai_risk_assessment?: boolean;
  has_ai_usage_documentation?: boolean;
  has_human_oversight_procedure?: boolean;
  // HinSchG
  has_whistleblower_channel?: boolean;
  has_whistleblower_policy?: boolean;
  // ArbSchG
  has_gefaehrdungsbeurteilung?: boolean;
  has_gefaehrdungsbeurteilung_documented?: boolean;
  has_first_aid_measures?: boolean;
  has_employee_safety_training?: boolean;
  // AGG
  has_anti_discrimination_policy?: boolean;
  has_agc_complaints_procedure?: boolean;
  // MiLoG
  has_working_time_records?: boolean;
  uses_subcontractors?: boolean;
  // LkSG
  has_lksg_policy_statement?: boolean;
  has_supplier_code_of_conduct?: boolean;
  has_supplier_risk_assessment?: boolean;
  has_lksg_complaints_procedure?: boolean;
  // TTDSG / TDDDG
  has_website?: boolean;
  has_cookie_banner?: boolean;
  has_cookie_policy?: boolean;
  // GwG
  is_aml_obligated_sector?: boolean;
  has_aml_risk_analysis?: boolean;
  has_aml_officer?: boolean;
  has_kyc_procedures?: boolean;
  // EU Data Act
  produces_connected_products?: boolean;
  provides_data_processing_services?: boolean;
  has_data_access_mechanism?: boolean;
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
  confidence: "HIGH" | "MEDIUM" | "LOW";
  confidence_reason?: string;
  source_url?: string;
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
  profile_completeness?: {
    score: number;
    score_percent: number;
    answered: number;
    relevant: number;
    unanswered_count: number;
    unanswered_fields: string[];
  };
  knowledge_base_versions?: Record<string, {
    fetched_at: string;
    source_file_hash: string;
    source_url: string;
  }>;
  inferred_assumptions?: string[];
  regulation_coverage?: Record<string, {
    law_chunks: number;
    guidance_chunks: number;
    total_chunks: number;
    unique_articles: number;
  }>;
  diagnostic_only?: boolean;
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
