"""merge multiple heads

Revision ID: f8a4b1c2d3e5
Revises: a126de2dca90, e7f3a8b9c1d2
Create Date: 2025-11-25 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a4b1c2d3e5'
down_revision: Union[str, Sequence[str], None] = ('a126de2dca90', 'e7f3a8b9c1d2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge migrations."""
    pass


def downgrade() -> None:
    """Downgrade merge."""
    pass
