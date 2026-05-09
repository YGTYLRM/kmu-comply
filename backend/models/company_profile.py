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
    missing_optional_fields: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
