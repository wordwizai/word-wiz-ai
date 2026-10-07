"""add phonics curriculum tables

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6g7
Create Date: 2026-10-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    if op.get_context().as_sql:  # offline (--sql) mode
        return False  # no database to inspect; emit the full DDL
    # main.py runs create_all at startup, so a deployed backend may already
    # have made these tables by the time this migration runs.
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    """Create pattern_sessions, assignments and assignment_students."""
    if not _has_table('pattern_sessions'):
        op.create_table(
            'pattern_sessions',
            sa.Column('session_id', sa.Integer(), nullable=False),
            sa.Column('pattern_slug', sa.String(length=64), nullable=False),
            sa.Column('words_correct', sa.Integer(), nullable=True),
            sa.Column('words_total', sa.Integer(), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('session_id'),
        )
        op.create_index(op.f('ix_pattern_sessions_pattern_slug'), 'pattern_sessions', ['pattern_slug'], unique=False)

    if not _has_table('assignments'):
        op.create_table(
            'assignments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('class_id', sa.Integer(), nullable=False),
            sa.Column('pattern_slug', sa.String(length=64), nullable=False),
            sa.Column('whole_class', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('class_id', 'pattern_slug', name='unique_class_pattern'),
        )
        op.create_index(op.f('ix_assignments_class_id'), 'assignments', ['class_id'], unique=False)

    if not _has_table('assignment_students'):
        op.create_table(
            'assignment_students',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('assignment_id', sa.Integer(), nullable=False),
            sa.Column('student_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('assignment_id', 'student_id', name='unique_assignment_student'),
        )
        op.create_index(op.f('ix_assignment_students_assignment_id'), 'assignment_students', ['assignment_id'], unique=False)
        op.create_index(op.f('ix_assignment_students_student_id'), 'assignment_students', ['student_id'], unique=False)


def downgrade() -> None:
    """Drop the phonics curriculum tables."""
    op.drop_table('assignment_students')
    op.drop_table('assignments')
    op.drop_table('pattern_sessions')
