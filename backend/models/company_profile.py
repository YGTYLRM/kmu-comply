from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class CompanyProfile(BaseModel):
    # Identity
    company_name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., description="Industry sector of the company")
    country: str = Field(default="DE", description="ISO 3166-1 alpha-2 country code")

    # Size indicators
    employee_count: int = Field(..., ge=1, le=1_000_000)
    annual_revenue_eur: Optional[float] = Field(
        None, ge=0, description="Annual revenue in EUR"
    )
    balance_sheet_total_eur: Optional[float] = Field(
        None, ge=0, description="Balance sheet total in EUR"
    )

    # Data processing
    processes_personal_data: bool = Field(
        ..., description="Does the company process personal data of EU residents?"
    )
    processes_special_category_data: bool = Field(
        default=False,
        description="Health, biometric, racial, political, or similar sensitive data",
    )
    processing_is_occasional: bool = Field(
        default=False,
        description="Is personal data processing only occasional/incidental?",
    )
    has_dpo: bool = Field(
        default=False, description="Does the company already have a Data Protection Officer?"
    )
    has_processing_records: bool = Field(
        default=False, description="Does the company maintain Records of Processing Activities?"
    )

    # Supply chain
    has_supply_chain_abroad: bool = Field(
        default=False, description="Does the company have suppliers or manufacturers abroad?"
    )
    supply_chain_countries: list[str] = Field(
        default_factory=list,
        description="Countries where direct suppliers are located (ISO codes)",
    )

    # Energy
    annual_energy_consumption_mwh: Optional[float] = Field(
        None, ge=0, description="Annual energy consumption in MWh"
    )
    has_energy_management_system: bool = Field(default=False)
    has_conducted_energy_audit: bool = Field(default=False)

    # Reporting / listing
    is_listed_company: bool = Field(
        default=False, description="Is the company listed on a regulated stock market?"
    )
    has_sustainability_report: bool = Field(default=False)

    # Technology (NIS2 / AI Act)
    is_critical_infrastructure_sector: bool = Field(
        default=False,
        description="Is the company in a critical or important sector under NIS2 (energy, transport, banking, health, digital infrastructure, etc.)?",
    )
    uses_ai_systems: bool = Field(
        default=False,
        description="Does the company develop, deploy, or operate AI systems?",
    )

    # ── GDPR / BDSG — policies & documentation ───────────────────────────────
    has_privacy_policy: Optional[bool] = Field(
        None, description="Does the company have a published privacy policy (Datenschutzerklärung)? — Art. 13/14 GDPR"
    )
    has_processor_agreements: Optional[bool] = Field(
        None, description="Are data processing agreements (AVV) in place with all vendors who process personal data? — Art. 28 GDPR"
    )
    has_data_breach_procedure: Optional[bool] = Field(
        None, description="Is there a documented data breach detection and notification procedure? — Art. 33/34 GDPR"
    )
    has_tom_documentation: Optional[bool] = Field(
        None, description="Are technical and organisational security measures (TOMs) documented? — Art. 32 GDPR"
    )
    has_data_retention_policy: Optional[bool] = Field(
        None, description="Is there a documented data retention and deletion policy? — Art. 5(1)(e) GDPR"
    )
    has_data_protection_training: Optional[bool] = Field(
        None, description="Do employees who handle personal data receive regular data protection training? — Art. 29/32(4) GDPR"
    )
    transfers_data_outside_eea: Optional[bool] = Field(
        None, description="Does the company transfer personal data to recipients outside the EEA? — Art. 44–49 GDPR"
    )
    has_consent_management: Optional[bool] = Field(
        None, description="Is consent properly obtained and documented where required (e.g. cookie consent, marketing)? — Art. 6/7 GDPR"
    )

    # ── NIS2 — cybersecurity measures ────────────────────────────────────────
    has_information_security_policy: Optional[bool] = Field(
        None, description="Does the company have a written information security policy? — Art. 21(2)(a) NIS2"
    )
    has_incident_response_plan: Optional[bool] = Field(
        None, description="Is there a documented incident response and handling plan? — Art. 21(2)(b) NIS2"
    )
    has_business_continuity_plan: Optional[bool] = Field(
        None, description="Does the company have a business continuity and disaster recovery plan? — Art. 21(2)(c) NIS2"
    )
    has_vulnerability_management: Optional[bool] = Field(
        None, description="Are regular vulnerability scans or penetration tests conducted? — Art. 21(2)(e) NIS2"
    )
    has_mfa_implemented: Optional[bool] = Field(
        None, description="Is multi-factor authentication (MFA) implemented for critical systems and remote access? — Art. 21(2)(j) NIS2"
    )
    has_supply_chain_security_assessment: Optional[bool] = Field(
        None, description="Are suppliers assessed for cybersecurity risks? — Art. 21(2)(d) NIS2"
    )
    has_security_awareness_training: Optional[bool] = Field(
        None, description="Do employees receive regular cybersecurity awareness training? — Art. 21(2)(g) NIS2"
    )

    # ── EU AI Act ─────────────────────────────────────────────────────────────
    ai_systems_are_high_risk: Optional[bool] = Field(
        None, description="Do any AI systems fall into a high-risk category under Annex III of the EU AI Act (e.g. hiring decisions, credit scoring, safety-critical systems)?"
    )
    has_ai_risk_assessment: Optional[bool] = Field(
        None, description="Has a risk assessment been conducted for AI systems in use? — Art. 9 EU AI Act"
    )
    has_ai_usage_documentation: Optional[bool] = Field(
        None, description="Is use of AI systems documented (purpose, data inputs, decision logic)? — Art. 13 EU AI Act"
    )
    has_human_oversight_procedure: Optional[bool] = Field(
        None, description="Are human oversight procedures documented and implemented for AI systems? — Art. 14 EU AI Act"
    )

    # ── HinSchG — whistleblower protection ───────────────────────────────────
    has_whistleblower_channel: Optional[bool] = Field(
        None, description="Does the company have an internal whistleblower reporting channel? — §12 HinSchG (mandatory ≥50 employees)"
    )
    has_whistleblower_policy: Optional[bool] = Field(
        None, description="Is there a documented whistleblower protection policy? — §13 HinSchG"
    )

    # ── ArbSchG — occupational health & safety ────────────────────────────────
    has_gefaehrdungsbeurteilung: Optional[bool] = Field(
        None, description="Has a workplace hazard/risk assessment (Gefährdungsbeurteilung) been conducted? — §5 ArbSchG (mandatory for all employers)"
    )
    has_gefaehrdungsbeurteilung_documented: Optional[bool] = Field(
        None, description="Is the hazard assessment documented in writing? — §6 ArbSchG"
    )
    has_first_aid_measures: Optional[bool] = Field(
        None, description="Are first aid measures and designated first aiders in place? — §10 ArbSchG"
    )
    has_employee_safety_training: Optional[bool] = Field(
        None, description="Do employees receive documented occupational safety instructions at onboarding and regularly thereafter? — §12 ArbSchG"
    )

    # ── AGG — anti-discrimination ─────────────────────────────────────────────
    has_anti_discrimination_policy: Optional[bool] = Field(
        None, description="Does the company have preventive anti-discrimination measures in place (policy, training)? — §12 AGG"
    )
    has_agc_complaints_procedure: Optional[bool] = Field(
        None, description="Is there a formal complaints procedure for discrimination cases? — §13 AGG"
    )

    # ── MiLoG — minimum wage ──────────────────────────────────────────────────
    has_working_time_records: Optional[bool] = Field(
        None, description="Are working time records maintained for all employees in covered sectors? — §17 MiLoG"
    )
    uses_subcontractors: Optional[bool] = Field(
        None, description="Does the company use subcontractors or service providers who provide labour? — §13 MiLoG (principal liability)"
    )

    # ── TTDSG — cookie / ePrivacy ─────────────────────────────────────────────
    has_website: bool = Field(
        default=True,
        description="Does the company operate a public-facing website or app accessible by users in Germany?",
    )
    has_cookie_banner: Optional[bool] = Field(
        None, description="Is a compliant cookie consent banner in place that blocks non-essential scripts until consent is given? — §25 TTDSG"
    )
    has_cookie_policy: Optional[bool] = Field(
        None, description="Is there a documented cookie policy listing all cookies, their purpose, and retention period? — §25 TTDSG / Art. 13 GDPR"
    )

    # ── GwG — anti-money laundering ───────────────────────────────────────────
    is_aml_obligated_sector: bool = Field(
        default=False,
        description="Is the company in an AML-obligated sector under §2 GwG (financial services, payment, insurance, real estate agents, lawyers, notaries, accountants, crypto exchanges, gambling)?",
    )
    has_aml_officer: Optional[bool] = Field(
        None, description="Has an AML compliance officer (Geldwäschebeauftragter) been appointed? — §7 GwG"
    )
    has_aml_risk_analysis: Optional[bool] = Field(
        None, description="Has a documented AML risk analysis been conducted? — §5 GwG"
    )
    has_kyc_procedures: Optional[bool] = Field(
        None, description="Are Know Your Customer (KYC) / customer due diligence procedures implemented? — §10 GwG"
    )

    # ── EU Data Act ───────────────────────────────────────────────────────────
    produces_connected_products: bool = Field(
        default=False,
        description="Does the company manufacture or place on the market connected (IoT) products that collect and process data? — Art. 3 EU Data Act",
    )
    provides_data_processing_services: bool = Field(
        default=False,
        description="Does the company provide cloud, edge, or other data processing services to business customers? — Art. 23 EU Data Act",
    )
    has_data_access_mechanism: Optional[bool] = Field(
        None, description="Is there a mechanism allowing users/customers to access data generated by connected products or services? — Art. 4 EU Data Act"
    )

    # ── LkSG — supply chain due diligence ────────────────────────────────────
    has_lksg_policy_statement: Optional[bool] = Field(
        None, description="Has the company published an LkSG policy statement (Grundsatzerklärung)? — §6 LkSG"
    )
    has_supplier_code_of_conduct: Optional[bool] = Field(
        None, description="Does the company have a supplier code of conduct covering human rights and environmental standards? — §6 LkSG"
    )
    has_supplier_risk_assessment: Optional[bool] = Field(
        None, description="Is a formal risk assessment of direct suppliers conducted at least annually? — §5 LkSG"
    )
    has_lksg_complaints_procedure: Optional[bool] = Field(
        None, description="Has an LkSG-compliant complaints mechanism been established? — §8 LkSG"
    )

    # Existing compliance measures (free text, optional)
    existing_compliance_notes: Optional[str] = Field(
        None, max_length=2000, description="Any existing compliance measures the company has"
    )

    @field_validator("company_name", "industry", mode="before")
    @classmethod
    def strip_and_limit(cls, v: str) -> str:
        return v.strip()[:200]

    @field_validator("existing_compliance_notes", mode="before")
    @classmethod
    def strip_notes(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        return cleaned if cleaned else None

    @model_validator(mode="after")
    def supply_chain_requires_abroad_flag(self) -> "CompanyProfile":
        if self.supply_chain_countries and not self.has_supply_chain_abroad:
            self.has_supply_chain_abroad = True
        return self


class EnrichedCompanyProfile(CompanyProfile):
    """Profile after Step 1 enrichment — adds inferred fields and validation notes."""

    inferred_characteristics: list[str] = Field(default_factory=list)
    # Assumptions inferred by the LLM — NOT confirmed by the user.
    # Must not be used as the sole basis for NON_COMPLIANT gap findings.
    inferred_assumptions: list[str] = Field(default_factory=list)
    missing_optional_fields: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
