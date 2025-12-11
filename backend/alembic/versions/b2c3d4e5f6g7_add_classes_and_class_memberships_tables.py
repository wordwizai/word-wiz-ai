"""add_classes_and_class_memberships_tables

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2024-12-11 06:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create classes and class_memberships tables."""
    # Create classes table
    op.create_table(
        'classes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('join_code', sa.String(length=10), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('join_code')
    )
    op.create_index(op.f('ix_classes_join_code'), 'classes', ['join_code'], unique=True)
    op.create_index(op.f('ix_classes_teacher_id'), 'classes', ['teacher_id'], unique=False)

    # Create class_memberships table
    op.create_table(
        'class_memberships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('class_id', 'student_id', name='unique_membership')
    )
    op.create_index(op.f('ix_class_memberships_class_id'), 'class_memberships', ['class_id'], unique=False)
    op.create_index(op.f('ix_class_memberships_student_id'), 'class_memberships', ['student_id'], unique=False)


def downgrade() -> None:
    """Drop classes and class_memberships tables."""
    op.drop_index(op.f('ix_class_memberships_student_id'), table_name='class_memberships')
    op.drop_index(op.f('ix_class_memberships_class_id'), table_name='class_memberships')
    op.drop_table('class_memberships')
    
    op.drop_index(op.f('ix_classes_teacher_id'), table_name='classes')
    op.drop_index(op.f('ix_classes_join_code'), table_name='classes')
    op.drop_table('classes')
