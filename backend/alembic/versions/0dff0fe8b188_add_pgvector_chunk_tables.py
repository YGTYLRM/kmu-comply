"""add_pgvector_chunk_tables

Revision ID: 0dff0fe8b188
Revises: c1d2e3f4a5b6
Create Date: 2026-08-16 22:00:00.000000

Phase 0 of the ChromaDB -> pgvector migration: schema only, no data
movement, nothing reads or writes these tables yet. See the migration
plan for the full phased design (dual-write in Phase 1, shadow-read +
eval gate in Phase 2, cutover in Phase 3-4).

regulation_chunks holds the 15 static regulation collections
(discriminated by `collection`, matching rag/ingest.py's
REGULATION_COLLECTIONS values) with one row per chunk, mirroring the
metadata rag/ingest.py already attaches to each chunk today.
company_doc_chunks is a separate, leaner table for the dynamic
per-analysis-job collections (rag/company_ingest.py) — different
lifecycle (created and deleted per job, no static provenance columns
needed).

Embedding dimension is 1024, matching the current embedding model
(intfloat/multilingual-e5-large, verified directly rather than assumed).
Cosine distance is used for the HNSW index to match the `hnsw:space:
cosine` metadata ChromaDB collections are created with today (rag/ingest.py,
rag/company_ingest.py), so retrieval scoring behavior is preserved.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = '0dff0fe8b188'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 1024


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'regulation_chunks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('collection', sa.String(length=50), nullable=False),
        sa.Column('regulation', sa.String(length=50), nullable=False),
        sa.Column('article_number', sa.String(length=50), nullable=False),
        sa.Column('paragraph', sa.String(length=20), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('document_type', sa.String(length=20), nullable=False),
        sa.Column('obligation_type', sa.String(length=20), nullable=True),
        sa.Column('source_file', sa.String(length=500), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('legal_version_date', sa.String(length=20), nullable=True),
        sa.Column('fetched_at', sa.String(length=40), nullable=True),
        sa.Column('source_file_hash', sa.String(length=20), nullable=True),
        sa.Column('content_hash', sa.String(length=20), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(EMBEDDING_DIM), nullable=False),
        sa.Column('metadata_extra', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_regulation_chunks_collection', 'regulation_chunks', ['collection'])
    op.create_index(
        'ix_regulation_chunks_collection_article',
        'regulation_chunks', ['collection', 'article_number'],
    )
    # Dedup / re-ingestion key — lets ingestion use ON CONFLICT DO UPDATE
    # keyed on content, replacing ChromaDB's positional chunk IDs (which go
    # stale on re-ingestion when a file's chunk count changes).
    op.create_unique_constraint(
        'uq_regulation_chunks_dedup',
        'regulation_chunks', ['collection', 'source_file', 'content_hash'],
    )
    op.execute(
        "CREATE INDEX ix_regulation_chunks_embedding ON regulation_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        'company_doc_chunks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('source_file', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(EMBEDDING_DIM), nullable=False),
        sa.Column('metadata_extra', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_company_doc_chunks_job_id', 'company_doc_chunks', ['job_id'])
    op.execute(
        "CREATE INDEX ix_company_doc_chunks_embedding ON company_doc_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_table('company_doc_chunks')
    op.drop_index('ix_regulation_chunks_embedding', table_name='regulation_chunks')
    op.drop_constraint('uq_regulation_chunks_dedup', 'regulation_chunks', type_='unique')
    op.drop_index('ix_regulation_chunks_collection_article', table_name='regulation_chunks')
    op.drop_index('ix_regulation_chunks_collection', table_name='regulation_chunks')
    op.drop_table('regulation_chunks')
    # Deliberately not dropping the vector extension — other tables/sessions
    # may depend on it by the time this downgrade runs, and CREATE EXTENSION
    # IF NOT EXISTS is idempotent so leaving it installed is harmless.
