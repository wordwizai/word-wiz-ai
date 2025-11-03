"""add_client_phoneme_extraction_setting

Revision ID: dae54bfc468d
Revises: 3644d5979f76
Create Date: 2025-11-02 11:51:43.470572

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dae54bfc468d'
down_revision: Union[str, Sequence[str], None] = '3644d5979f76'
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
        if 'use_client_phoneme_extraction' not in columns:
            # Add use_client_phoneme_extraction column to user_settings table
            # Use server_default for MySQL compatibility
            op.add_column('user_settings', 
                sa.Column('use_client_phoneme_extraction', sa.Boolean(), 
                         nullable=False, server_default='1'))
            print("Added use_client_phoneme_extraction column with default TRUE")
        else:
            print("Column use_client_phoneme_extraction already exists")
            # Update any NULL values to TRUE for existing rows
            op.execute('UPDATE user_settings SET use_client_phoneme_extraction = 1 WHERE use_client_phoneme_extraction IS NULL')
            print("Updated NULL values to TRUE")
    else:
        print("Warning: user_settings table does not exist, skipping migration")


def downgrade() -> None:
    """Downgrade schema."""
    # Check if user_settings table exists before dropping column
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'user_settings' in inspector.get_table_names():
        # Remove use_client_phoneme_extraction column from user_settings table
        op.drop_column('user_settings', 'use_client_phoneme_extraction')
