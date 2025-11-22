"""Increase emoji_icon length for Lucide icons

Revision ID: a126de2dca90
Revises: dae54bfc468d
Create Date: 2025-11-22 14:02:22.615961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'a126de2dca90'
down_revision: Union[str, Sequence[str], None] = 'dae54bfc468d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change emoji_icon column from VARCHAR(10) to VARCHAR(100)
    op.alter_column('activities', 'emoji_icon',
                    existing_type=sa.String(length=10),
                    type_=sa.String(length=100),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Change emoji_icon column back from VARCHAR(100) to VARCHAR(10)
    op.alter_column('activities', 'emoji_icon',
                    existing_type=sa.String(length=100),
                    type_=sa.String(length=10),
                    existing_nullable=True)
