"""add_assigned_to_expert_reviews

Revision ID: a3f1e9c2b847
Revises: f85c52ab4d63
Create Date: 2026-06-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f1e9c2b847'
down_revision: Union[str, None] = 'f85c52ab4d63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('expert_review_requests', sa.Column('assigned_to', sa.String(320), nullable=True))
    op.add_column('expert_review_requests', sa.Column('reviewer_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('expert_review_requests', 'reviewer_notes')
    op.drop_column('expert_review_requests', 'assigned_to')
