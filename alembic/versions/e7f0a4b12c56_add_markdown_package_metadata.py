"""add markdown_package_metadata table

Revision ID: e7f0a4b12c56
Revises: 447b08563f58
Create Date: 2026-07-02 10:41:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f0a4b12c56'
down_revision: Union[str, Sequence[str], None] = '447b08563f58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'markdown_package_metadata',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('lead_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('generator_version', sa.String(length=100), nullable=False,
                  server_default='leadforge-markdown-engine-1.0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('website_type', sa.String(length=100), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('style', sa.String(length=100), nullable=True),
        sa.Column('estimated_total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('document_count', sa.Integer(), nullable=False, server_default='12'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_markdown_package_metadata_id'), 'markdown_package_metadata', ['id'], unique=False)
    op.create_index(op.f('ix_markdown_package_metadata_lead_id'), 'markdown_package_metadata', ['lead_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_markdown_package_metadata_lead_id'), table_name='markdown_package_metadata')
    op.drop_index(op.f('ix_markdown_package_metadata_id'), table_name='markdown_package_metadata')
    op.drop_table('markdown_package_metadata')
