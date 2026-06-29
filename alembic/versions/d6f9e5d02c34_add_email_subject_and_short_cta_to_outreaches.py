"""add email_subject and short_cta to outreach

Revision ID: d6f9e5d02c34
Revises: c5f8e4d01b23
Create Date: 2026-06-27 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6f9e5d02c34'
down_revision: Union[str, None] = 'c5f8e4d01b23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('outreaches', sa.Column('email_subject', sa.Text(), nullable=True))
    op.add_column('outreaches', sa.Column('short_cta', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('outreaches', 'short_cta')
    op.drop_column('outreaches', 'email_subject')
