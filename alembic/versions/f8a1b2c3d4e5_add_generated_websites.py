"""add generated websites

Revision ID: f8a1b2c3d4e5
Revises: 1a6f7a805ee9
Create Date: 2026-07-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "1a6f7a805ee9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generated_websites",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("generation_id", sa.String(length=64), nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=True),
        sa.Column("framework", sa.String(length=50), nullable=False, server_default="static-html"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="generated"),
        sa.Column("html", sa.Text(), nullable=False),
        sa.Column("preview_path", sa.String(length=255), nullable=False),
        sa.Column("package_id", sa.String(length=64), nullable=True),
        sa.Column("package_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("build_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generated_websites_id"), "generated_websites", ["id"], unique=False)
    op.create_index(op.f("ix_generated_websites_lead_id"), "generated_websites", ["lead_id"], unique=False)
    op.create_index(op.f("ix_generated_websites_generation_id"), "generated_websites", ["generation_id"], unique=False)
    op.create_index(op.f("ix_generated_websites_package_id"), "generated_websites", ["package_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_generated_websites_package_id"), table_name="generated_websites")
    op.drop_index(op.f("ix_generated_websites_generation_id"), table_name="generated_websites")
    op.drop_index(op.f("ix_generated_websites_lead_id"), table_name="generated_websites")
    op.drop_index(op.f("ix_generated_websites_id"), table_name="generated_websites")
    op.drop_table("generated_websites")
