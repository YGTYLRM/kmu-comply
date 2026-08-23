"""add_admin_audit_log

Revision ID: c1d2e3f4a5b6
Revises: a3f1e9c2b847
Create Date: 2026-06-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'a3f1e9c2b847'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'admin_audit_log',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('actor_fingerprint', sa.String(length=16), nullable=False),
        sa.Column('actor_ip', sa.String(length=64), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('detail', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_admin_audit_log_actor_fingerprint', 'admin_audit_log', ['actor_fingerprint'])
    op.create_index('ix_admin_audit_log_created_at', 'admin_audit_log', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_admin_audit_log_created_at', table_name='admin_audit_log')
    op.drop_index('ix_admin_audit_log_actor_fingerprint', table_name='admin_audit_log')
    op.drop_table('admin_audit_log')
