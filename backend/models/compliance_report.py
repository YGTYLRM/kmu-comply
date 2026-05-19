from typing import Optional
from pydantic import BaseModel, Field
from models.enums import (
    Regulation,
    ComplianceStatus,
    Priority,
    ObligationType,
)


class RegulationApplicability(BaseModel):
    regulation: Regulation
    applies: bool
    reason: str
    key_threshold: Optional[str] = None


class RegulatoryChunk(BaseModel):
    """A single retrieved regulatory article chunk from ChromaDB."""

    regulation: Regulation
    article_number: str
    title: str
    text: str
    obligation_type: ObligationType
    applicable_to: list[str] = Field(default_factory=list)
    threshold: Optional[str] = None
    source_url: Optional[str] = None
    document_type: str = "law"  # "law" | "guidance" — controls source authority in prompts


class ComplianceGap(BaseModel):
    regulation: Regulation
    article_number: str
    article_title: str
    status: ComplianceStatus
    evidence: str = Field(..., description="Explanation of WHY this status was assigned")
    deficiency_description: Optional[str] = None
    confidence: str = "HIGH"          # HIGH | MEDIUM | LOW
    confidence_reason: Optional[str] = None
    source_url: Optional[str] = None  # official source URL for this regulation


class ActionItem(BaseModel):
    regulation: Regulation
    article_number: str
    action: str
    priority: Priority
    source_url: Optional[str] = None  # official source URL for this regulation
    estimated_effort: str = Field(
        ..., description="e.g., '2-4 hours', '1-2 weeks', '1 FTE-month'"
    )
    deadline: Optional[str] = None
    dependencies: list[str] = Field(default_factory=list)
    gap_reference: str = Field(..., description="Points back to the ComplianceGap this resolves")


class RegulationScore(BaseModel):
    regulation: Regulation
    total_requirements: int
    compliant: int
    partially_compliant: int
    non_compliant: int
    cannot_assess: int
    # compliance_score: only counts COMPLIANT/PARTIALLY_COMPLIANT/NON_COMPLIANT (excludes CANNOT_ASSESS)
    # CANNOT_ASSESS items do NOT contribute — unknown compliance is not half-compliance
    score_percent: float = Field(..., ge=0, le=100)
    # assessment_completeness: ratio of assessed items (CANNOT_ASSESS lowers this, not the score)
    assessment_completeness_percent: float = Field(default=100.0, ge=0, le=100)


class ComplianceReport(BaseModel):
    job_id: str
    company_name: str
    generated_at: str

    # Section 2 — profile summary
    applicable_regulations: list[RegulationApplicability]
    inferred_characteristics: list[str]
    inferred_assumptions: list[str] = Field(default_factory=list)
    missing_optional_fields: list[str]
    validation_warnings: list[str]

    # Section 4 — detailed analysis
    retrieved_chunks: list[RegulatoryChunk]
    gap_analysis: list[ComplianceGap]

    # Section 5 — action plan
    action_plan: list[ActionItem]

    # Section 6 — scores
    regulation_scores: list[RegulationScore]
    overall_score_percent: float = Field(..., ge=0, le=100)

    # Section 1 — executive summary (assembled last)
    executive_summary: str = Field(default="")

    # Profile completeness
    profile_completeness: Optional[dict] = None

    # Knowledge base versioning — maps regulation → {fetched_at, source_file_hash, source_url}
    knowledge_base_versions: Optional[dict] = None

    # Per-regulation source coverage — maps regulation → {law_chunks, guidance_chunks, company_doc_chunks}
    # Shows users how well-grounded each regulation's analysis is
    regulation_coverage: Optional[dict] = None

    # Analysis versioning — for reproducibility and audit trail
    rule_engine_version: Optional[str] = None
    prompt_version: Optional[str] = None

    # Meta
    disclaimer: str = Field(
        default=(
            "Dieser Bericht wird von einem automatisierten KI-System ausschließlich für vorläufige Screening-Zwecke erstellt. "
            "Er stellt keine Rechtsberatung, kein Rechtsgutachten und keine formelle Rechtsbewertung dar. "
            "Durch die Nutzung dieses Dienstes wird kein Mandatsverhältnis begründet. "
            "Regulatorische Schwellenwerte und Pflichten basieren auf dem zum Zeitpunkt der Dateneingabe geltenden Recht "
            "und spiegeln möglicherweise keine neueren Gesetzesänderungen oder Gerichtsurteile wider. "
            "Überprüfen Sie alle Compliance-Anforderungen stets mit einem qualifizierten deutschen Rechtsanwalt oder "
            "Steuerberater, bevor Sie Maßnahmen ergreifen oder unterlassen. "
            "Complio übernimmt keine Haftung für Entscheidungen, die auf Basis dieses Berichts getroffen werden."
        )
    )
    requires_manual_review: list[str] = Field(
        default_factory=list,
        description="Steps or sections that failed validation and need human review",
    )
