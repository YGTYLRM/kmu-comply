"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "companies",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("industry", sa.String(200), nullable=True),
        sa.Column("country", sa.String(10), nullable=False, server_default="DE"),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("annual_revenue_eur", sa.Float(), nullable=True),
        sa.Column("balance_sheet_total_eur", sa.Float(), nullable=True),
        sa.Column("processes_personal_data", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("processes_special_category_data", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("processing_is_occasional", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_dpo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_processing_records", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_supply_chain_abroad", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("supply_chain_countries", sa.JSON(), nullable=True),
        sa.Column("annual_energy_consumption_mwh", sa.Float(), nullable=True),
        sa.Column("has_energy_management_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_conducted_energy_audit", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_listed_company", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_sustainability_report", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_critical_infrastructure_sector", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("uses_ai_systems", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_privacy_policy", sa.Boolean(), nullable=True),
        sa.Column("has_processor_agreements", sa.Boolean(), nullable=True),
        sa.Column("has_data_breach_procedure", sa.Boolean(), nullable=True),
        sa.Column("has_tom_documentation", sa.Boolean(), nullable=True),
        sa.Column("has_data_retention_policy", sa.Boolean(), nullable=True),
        sa.Column("has_data_protection_training", sa.Boolean(), nullable=True),
        sa.Column("transfers_data_outside_eea", sa.Boolean(), nullable=True),
        sa.Column("has_consent_management", sa.Boolean(), nullable=True),
        sa.Column("has_information_security_policy", sa.Boolean(), nullable=True),
        sa.Column("has_incident_response_plan", sa.Boolean(), nullable=True),
        sa.Column("has_business_continuity_plan", sa.Boolean(), nullable=True),
        sa.Column("has_vulnerability_management", sa.Boolean(), nullable=True),
        sa.Column("has_mfa_implemented", sa.Boolean(), nullable=True),
        sa.Column("has_supply_chain_security_assessment", sa.Boolean(), nullable=True),
        sa.Column("has_security_awareness_training", sa.Boolean(), nullable=True),
        sa.Column("ai_systems_are_high_risk", sa.Boolean(), nullable=True),
        sa.Column("has_ai_risk_assessment", sa.Boolean(), nullable=True),
        sa.Column("has_ai_usage_documentation", sa.Boolean(), nullable=True),
        sa.Column("has_human_oversight_procedure", sa.Boolean(), nullable=True),
        sa.Column("has_gefaehrdungsbeurteilung", sa.Boolean(), nullable=True),
        sa.Column("has_gefaehrdungsbeurteilung_documented", sa.Boolean(), nullable=True),
        sa.Column("has_first_aid_measures", sa.Boolean(), nullable=True),
        sa.Column("has_employee_safety_training", sa.Boolean(), nullable=True),
        sa.Column("has_anti_discrimination_policy", sa.Boolean(), nullable=True),
        sa.Column("has_agc_complaints_procedure", sa.Boolean(), nullable=True),
        sa.Column("has_working_time_records", sa.Boolean(), nullable=True),
        sa.Column("uses_subcontractors", sa.Boolean(), nullable=True),
        sa.Column("has_whistleblower_channel", sa.Boolean(), nullable=True),
        sa.Column("has_whistleblower_policy", sa.Boolean(), nullable=True),
        sa.Column("has_lksg_policy_statement", sa.Boolean(), nullable=True),
        sa.Column("has_supplier_code_of_conduct", sa.Boolean(), nullable=True),
        sa.Column("has_supplier_risk_assessment", sa.Boolean(), nullable=True),
        sa.Column("has_lksg_complaints_procedure", sa.Boolean(), nullable=True),
        sa.Column("existing_compliance_notes", sa.Text(), nullable=True),
        sa.Column("profile_raw", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_companies_user_id", "companies", ["user_id"])

    op.create_table(
        "reports",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.String(), unique=True, nullable=True),
        sa.Column("overall_score_percent", sa.Float(), nullable=True),
        sa.Column("triggered_by", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_reports_company_id", "reports", ["company_id"])
    op.create_index("ix_reports_job_id", "reports", ["job_id"])

    op.create_table(
        "gap_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("report_id", sa.String(), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("regulation", sa.String(100), nullable=False),
        sa.Column("article_number", sa.String(50), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("finding", sa.Text(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
    )
    op.create_index("ix_gap_items_report_id", "gap_items", ["report_id"])

    op.create_table(
        "action_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(20), nullable=True),
        sa.Column("regulation", sa.String(100), nullable=True),
        sa.Column("effort", sa.String(20), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_action_items_company_id", "action_items", ["company_id"])

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("stripe_customer_id", sa.String(), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(), unique=True, nullable=True),
        sa.Column("plan", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=True, index=True),
        sa.Column("company_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("current_step", sa.String(50), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])

    op.create_table(
        "action_completions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False, index=True),
        sa.Column("job_id", sa.String(), nullable=False, index=True),
        sa.Column("regulation", sa.String(100), nullable=False),
        sa.Column("article_number", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "rate_limit_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False, index=True),
        sa.Column("endpoint", sa.String(100), nullable=False),
        sa.Column("called_at", sa.DateTime(), nullable=False, index=True),
    )

    op.create_table(
        "expert_review_requests",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False, index=True),
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column("user_email", sa.String(320), nullable=True),
        sa.Column("focus_items", sa.JSON(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "pending_regulation_updates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("regulation", sa.String(100), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("new_hash", sa.String(64), nullable=False),
        sa.Column("previous_hash", sa.String(64), nullable=True),
        sa.Column("staging_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("first_approved_by", sa.String(200), nullable=True),
        sa.Column("first_approved_at", sa.DateTime(), nullable=True),
        sa.Column("first_approver_ip", sa.String(64), nullable=True),
        sa.Column("second_approved_by", sa.String(200), nullable=True),
        sa.Column("second_approved_at", sa.DateTime(), nullable=True),
        sa.Column("requires_second_approval", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("pending_regulation_updates")
    op.drop_table("expert_review_requests")
    op.drop_table("rate_limit_events")
    op.drop_table("action_completions")
    op.drop_table("jobs")
    op.drop_table("notifications")
    op.drop_table("subscriptions")
    op.drop_table("action_items")
    op.drop_table("gap_items")
    op.drop_table("reports")
    op.drop_table("companies")
    op.drop_table("profiles")
