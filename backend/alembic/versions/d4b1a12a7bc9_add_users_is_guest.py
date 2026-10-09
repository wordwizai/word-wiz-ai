"""add users.is_guest

Revision ID: d4b1a12a7bc9
Revises: c4d5e6f7a8b9
Create Date: 2026-10-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4b1a12a7bc9'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Every existing row is a real account. server_default fills them in, and
    # '0' works on both MySQL and SQLite.
    op.add_column(
        'users',
        sa.Column('is_guest', sa.Boolean(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Guest rows have no email or password, so drop them with the column
    # rather than leaving them to look like broken accounts.
    op.execute('DELETE FROM users WHERE is_guest = 1')
    op.drop_column('users', 'is_guest')
