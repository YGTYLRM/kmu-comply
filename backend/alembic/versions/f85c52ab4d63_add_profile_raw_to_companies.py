"""add_profile_raw_to_companies

Revision ID: f85c52ab4d63
Revises: 0001
Create Date: 2026-06-03 16:42:30.176589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f85c52ab4d63'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op: 0001_initial_schema.py already defines companies.profile_raw
    # (it was added to that file after this migration was first written).
    # Running the original op.add_column here against a fresh DB fails with
    # DuplicateColumnError. Kept as a no-op rather than deleted so later
    # migrations that chain off this revision ID still apply cleanly.
    pass


def downgrade() -> None:
    pass
