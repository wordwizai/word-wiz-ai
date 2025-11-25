"""add_use_websocket_setting

Revision ID: e7f3a8b9c1d2
Revises: dae54bfc468d
Create Date: 2025-11-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f3a8b9c1d2'
down_revision: Union[str, Sequence[str], None] = 'dae54bfc468d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if user_settings table exists before adding column
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'user_settings' in inspector.get_table_names():
        # Check if column already exists
        columns = [col['name'] for col in inspector.get_columns('user_settings')]
        if 'use_websocket' not in columns:
            # Add use_websocket column to user_settings table
            # Default to FALSE for gradual rollout (server_default for MySQL compatibility)
            op.add_column('user_settings', 
                sa.Column('use_websocket', sa.Boolean(), 
                         nullable=False, server_default='0'))
            print("Added use_websocket column with default FALSE")
        else:
            print("Column use_websocket already exists")
            # Update any NULL values to FALSE for existing rows
            op.execute('UPDATE user_settings SET use_websocket = 0 WHERE use_websocket IS NULL')
            print("Updated NULL values to FALSE")
    else:
        print("Warning: user_settings table does not exist, skipping migration")


def downgrade() -> None:
    """Downgrade schema."""
    # Check if user_settings table exists before dropping column
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'user_settings' in inspector.get_table_names():
        # Remove use_websocket column from user_settings table
        op.drop_column('user_settings', 'use_websocket')
