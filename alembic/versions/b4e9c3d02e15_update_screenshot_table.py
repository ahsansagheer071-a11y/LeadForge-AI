"""update screenshot table

Revision ID: b4e9c3d02e15
Revises: a3f8b2c91d04
Create Date: 2026-06-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4e9c3d02e15'
down_revision: Union[str, None] = 'a3f8b2c91d04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old columns
    op.drop_column('screenshots', 'local_path')
    op.drop_column('screenshots', 'cloudinary_url')

    # Add Desktop columns
    op.add_column('screenshots', sa.Column('desktop_local_path', sa.String(length=1000), nullable=True))
    op.add_column('screenshots', sa.Column('desktop_cloudinary_url', sa.String(length=2083), nullable=True))
    op.add_column('screenshots', sa.Column('desktop_public_id', sa.String(length=255), nullable=True))

    # Add Mobile columns
    op.add_column('screenshots', sa.Column('mobile_local_path', sa.String(length=1000), nullable=True))
    op.add_column('screenshots', sa.Column('mobile_cloudinary_url', sa.String(length=2083), nullable=True))
    op.add_column('screenshots', sa.Column('mobile_public_id', sa.String(length=255), nullable=True))

    # Add Full Page columns
    op.add_column('screenshots', sa.Column('full_page_local_path', sa.String(length=1000), nullable=True))
    op.add_column('screenshots', sa.Column('full_page_cloudinary_url', sa.String(length=2083), nullable=True))
    op.add_column('screenshots', sa.Column('full_page_public_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Drop new columns
    op.drop_column('screenshots', 'full_page_public_id')
    op.drop_column('screenshots', 'full_page_cloudinary_url')
    op.drop_column('screenshots', 'full_page_local_path')

    op.drop_column('screenshots', 'mobile_public_id')
    op.drop_column('screenshots', 'mobile_cloudinary_url')
    op.drop_column('screenshots', 'mobile_local_path')

    op.drop_column('screenshots', 'desktop_public_id')
    op.drop_column('screenshots', 'desktop_cloudinary_url')
    op.drop_column('screenshots', 'desktop_local_path')

    # Add old columns back
    op.add_column('screenshots', sa.Column('cloudinary_url', sa.VARCHAR(length=2083), autoincrement=False, nullable=True))
    op.add_column('screenshots', sa.Column('local_path', sa.VARCHAR(length=1000), autoincrement=False, nullable=True))
