"""update_websocket_and_client_extraction_defaults

Revision ID: a1b2c3d4e5f6
Revises: f8a4b1c2d3e5
Create Date: 2025-11-25 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f8a4b1c2d3e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - set correct defaults for websocket and client extraction."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'user_settings' in inspector.get_table_names():
        # Update use_websocket to TRUE for all existing users
        op.execute('UPDATE user_settings SET use_websocket = 1')
        print("Updated all users to use_websocket = TRUE")
        
        # Update use_client_phoneme_extraction to FALSE for all existing users
        op.execute('UPDATE user_settings SET use_client_phoneme_extraction = 0')
        print("Updated all users to use_client_phoneme_extraction = FALSE")
    else:
        print("Warning: user_settings table does not exist, skipping migration")


def downgrade() -> None:
    """Downgrade schema - revert to previous defaults."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'user_settings' in inspector.get_table_names():
        # Revert to old defaults
        op.execute('UPDATE user_settings SET use_websocket = 0')
        op.execute('UPDATE user_settings SET use_client_phoneme_extraction = 1')
        print("Reverted to old defaults")
