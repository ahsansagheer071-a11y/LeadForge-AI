"""Add provider_used to generation_jobs and widen business_name.

Revision ID: a1b2c3d4e5f6
Revises: f8a1b2c3d4e5
Create Date: 2025-07-11
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "f8a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generation_jobs",
        sa.Column("provider_used", sa.String(64), nullable=True),
    )
    op.alter_column(
        "website_intelligence",
        "business_name",
        existing_type=sa.String(100),
        type_=sa.String(255),
    )


def downgrade() -> None:
    op.drop_column("generation_jobs", "provider_used")
    op.alter_column(
        "website_intelligence",
        "business_name",
        existing_type=sa.String(255),
        type_=sa.String(100),
    )
