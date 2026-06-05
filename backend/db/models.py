import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Float, Integer, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


def _now():
    return datetime.utcnow()


def _uuid():
    return str(uuid.uuid4())


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # = supabase auth user id
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    companies: Mapped[list["Company"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    subscription: Mapped[Optional["Subscription"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)

    # Identity
    name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    country: Mapped[str] = mapped_column(String(10), default="DE")

    # Size
    employee_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    annual_revenue_eur: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    balance_sheet_total_eur: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Data processing
    processes_personal_data: Mapped[bool] = mapped_column(Boolean, default=False)
    processes_special_category_data: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_is_occasional: Mapped[bool] = mapped_column(Boolean, default=False)
    has_dpo: Mapped[bool] = mapped_column(Boolean, default=False)
    has_processing_records: Mapped[bool] = mapped_column(Boolean, default=False)

    # Supply chain
    has_supply_chain_abroad: Mapped[bool] = mapped_column(Boolean, default=False)
    supply_chain_countries: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    annual_energy_consumption_mwh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    has_energy_management_system: Mapped[bool] = mapped_column(Boolean, default=False)
    has_conducted_energy_audit: Mapped[bool] = mapped_column(Boolean, default=False)

    # Governance
    is_listed_company: Mapped[bool] = mapped_column(Boolean, default=False)
    has_sustainability_report: Mapped[bool] = mapped_column(Boolean, default=False)
    is_critical_infrastructure_sector: Mapped[bool] = mapped_column(Boolean, default=False)
    uses_ai_systems: Mapped[bool] = mapped_column(Boolean, default=False)

    # Privacy & policies
    has_privacy_policy: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_processor_agreements: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_data_breach_procedure: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_tom_documentation: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_data_retention_policy: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_data_protection_training: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    transfers_data_outside_eea: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_consent_management: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Security
    has_information_security_policy: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_incident_response_plan: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_business_continuity_plan: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_vulnerability_management: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_mfa_implemented: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_supply_chain_security_assessment: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_security_awareness_training: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # AI Act
    ai_systems_are_high_risk: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_ai_risk_assessment: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_ai_usage_documentation: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_human_oversight_procedure: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Workplace
    has_gefaehrdungsbeurteilung: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_gefaehrdungsbeurteilung_documented: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_first_aid_measures: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_employee_safety_training: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_anti_discrimination_policy: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_agc_complaints_procedure: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_working_time_records: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    uses_subcontractors: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_whistleblower_channel: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_whistleblower_policy: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_lksg_policy_statement: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_supplier_code_of_conduct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_supplier_risk_assessment: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_lksg_complaints_procedure: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    existing_compliance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Full profile JSON snapshot — source of truth for re-assessment and template generation
    # Eliminates reliance on disk-only _profile.json files which break on volume failure
    profile_raw: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    user: Mapped["Profile"] = relationship(back_populates="companies")
    reports: Mapped[list["Report"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    action_items: Mapped[list["ActionItem"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    overall_score_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(20), default="manual")
    raw_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    company: Mapped["Company"] = relationship(back_populates="reports")
    gap_items: Mapped[list["GapItem"]] = relationship(back_populates="report", cascade="all, delete-orphan")


class GapItem(Base):
    __tablename__ = "gap_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(String, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    regulation: Mapped[str] = mapped_column(String(100))
    article_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30))
    finding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    report: Mapped["Report"] = relationship(back_populates="gap_items")


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    regulation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    effort: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    company: Mapped["Company"] = relationship(back_populates="action_items")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, unique=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True)
    plan: Mapped[str] = mapped_column(String(30), nullable=False)          # starter | professional | enterprise
    status: Mapped[str] = mapped_column(String(20), nullable=False)        # active | canceled | past_due | trialing
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    user: Mapped["Profile"] = relationship(back_populates="subscription")


class JobRecord(Base):
    """Persistent job state — survives backend restarts."""
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)   # = job_id (UUID)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    company_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|running|completed|failed|partial
    current_step: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class ExpertReviewRequest(Base):
    """User request for expert (lawyer/consultant) review of compliance findings."""
    __tablename__ = "expert_review_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    job_id: Mapped[str] = mapped_column(String, nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    user_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    # Which specific findings to review (JSON list of {regulation, article_number})
    focus_items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|in_review|completed
    assigned_to: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class PendingRegulationUpdate(Base):
    """Staged regulation download awaiting human approval before KB update."""
    __tablename__ = "pending_regulation_updates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    regulation: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    new_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    staging_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|awaiting_second|approved|rejected
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Audit trail — who approved/rejected, from where
    first_approved_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    first_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    first_approver_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    second_approved_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    second_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    requires_second_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ActionCompletion(Base):
    __tablename__ = "action_completions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    job_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    regulation: Mapped[str] = mapped_column(String(100), nullable=False)
    article_number: Mapped[str] = mapped_column(String(50), nullable=False)
    # status: open | in_progress | done
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class RateLimitEvent(Base):
    __tablename__ = "rate_limit_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    called_at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(50))
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    user: Mapped["Profile"] = relationship(back_populates="notifications")
