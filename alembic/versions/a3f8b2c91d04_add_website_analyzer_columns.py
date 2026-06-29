"""add website analyzer columns to audits

Revision ID: a3f8b2c91d04
Revises: 27407898bb22
Create Date: 2026-06-26 22:27:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3f8b2c91d04"
down_revision: Union[str, None] = "27407898bb22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Website Analyzer – General
    op.add_column("audits", sa.Column("website_language", sa.String(20), nullable=True))
    op.add_column("audits", sa.Column("https_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("audits", sa.Column("http_status_code", sa.Integer(), nullable=True))

    # Website Analyzer – Content Counts
    op.add_column("audits", sa.Column("h1_count", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("audits", sa.Column("h2_count", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("audits", sa.Column("total_paragraphs", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("audits", sa.Column("total_images", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("audits", sa.Column("total_forms", sa.Integer(), nullable=False, server_default=sa.text("0")))

    # Website Analyzer – Navigation
    op.add_column("audits", sa.Column("contact_page_exists", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("audits", sa.Column("about_page_exists", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    # Website Analyzer – Social Presence
    op.add_column("audits", sa.Column("social_facebook", sa.String(500), nullable=True))
    op.add_column("audits", sa.Column("social_instagram", sa.String(500), nullable=True))
    op.add_column("audits", sa.Column("social_linkedin", sa.String(500), nullable=True))
    op.add_column("audits", sa.Column("social_twitter", sa.String(500), nullable=True))
    op.add_column("audits", sa.Column("social_youtube", sa.String(500), nullable=True))

    # Website Analyzer – SEO Flags
    op.add_column("audits", sa.Column("missing_meta_description", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("audits", sa.Column("missing_h1", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("audits", sa.Column("missing_title", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    # Website Analyzer – Performance
    op.add_column("audits", sa.Column("html_size_kb", sa.Float(), nullable=True))
    op.add_column("audits", sa.Column("response_time_ms", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("audits", "response_time_ms")
    op.drop_column("audits", "html_size_kb")
    op.drop_column("audits", "missing_title")
    op.drop_column("audits", "missing_h1")
    op.drop_column("audits", "missing_meta_description")
    op.drop_column("audits", "social_youtube")
    op.drop_column("audits", "social_twitter")
    op.drop_column("audits", "social_linkedin")
    op.drop_column("audits", "social_instagram")
    op.drop_column("audits", "social_facebook")
    op.drop_column("audits", "about_page_exists")
    op.drop_column("audits", "contact_page_exists")
    op.drop_column("audits", "total_forms")
    op.drop_column("audits", "total_images")
    op.drop_column("audits", "total_paragraphs")
    op.drop_column("audits", "h2_count")
    op.drop_column("audits", "h1_count")
    op.drop_column("audits", "http_status_code")
    op.drop_column("audits", "https_enabled")
    op.drop_column("audits", "website_language")
