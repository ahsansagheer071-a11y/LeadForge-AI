"""add explanation to lead_scores

Revision ID: c5f8e4d01b23
Revises: b4e9c3d02e15
Create Date: 2026-06-27 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5f8e4d01b23'
down_revision: Union[str, None] = 'b4e9c3d02e15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('lead_scores', sa.Column('explanation', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('lead_scores', 'explanation')
