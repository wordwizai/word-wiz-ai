"""add_gamification_tables

Revision ID: 48485c050cb8
Revises: b2c3d4e5f6g7
Create Date: 2026-04-14 22:43:49.379321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '48485c050cb8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    from sqlalchemy import inspect
    bind = op.get_bind()
    insp = inspect(bind)
    existing = insp.get_table_names()

    # achievement_definitions may already exist (created by Base.metadata.create_all)
    if 'achievement_definitions' not in existing:
        op.create_table('achievement_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(64), nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('icon_name', sa.String(64), nullable=False),
        sa.Column('xp_reward', sa.Integer(), nullable=False),
        sa.Column('trigger_type', sa.Enum('SESSIONS_COMPLETED', 'STREAK_DAYS', 'WORDS_READ', 'PERFECT_WORDS', 'PERFECT_SENTENCES', 'PER_IMPROVEMENT', 'LEVEL_REACHED', 'ALL_MODES_TRIED', 'STORY_COMPLETED', 'FREEZE_USED', 'MANUAL', name='achievementtrigger'), nullable=False),
        sa.Column('threshold_value', sa.Integer(), nullable=True),
        sa.Column('rarity', sa.Enum('common', 'rare', 'epic', 'legendary', name='achievementrarity'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_achievement_definitions_id'), 'achievement_definitions', ['id'], unique=False)
        op.create_index(op.f('ix_achievement_definitions_key'), 'achievement_definitions', ['key'], unique=True)

    if 'user_achievements' not in existing:
        op.create_table('user_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('earned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('xp_at_earn_time', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievement_definitions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievement')
        )
        op.create_index(op.f('ix_user_achievements_id'), 'user_achievements', ['id'], unique=False)
        op.create_index(op.f('ix_user_achievements_user_id'), 'user_achievements', ['user_id'], unique=False)

    if 'user_gamification' not in existing:
        op.create_table('user_gamification',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_xp', sa.Integer(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('streak_freezes_available', sa.Integer(), nullable=False),
        sa.Column('lifetime_badges_count', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id')
        )

    if 'xp_transactions' not in existing:
        op.create_table('xp_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Enum('SESSION_COMPLETE', 'PERFECT_WORD', 'PERFECT_SENTENCE', 'DAILY_PRACTICE', 'STREAK_BONUS', 'BADGE_EARNED', 'STREAK_FREEZE_AWARDED', name='xpreason'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_xp_transactions_id'), 'xp_transactions', ['id'], unique=False)
        op.create_index(op.f('ix_xp_transactions_user_id'), 'xp_transactions', ['user_id'], unique=False)

    # Index changes on classes (guard against already existing)
    existing_indexes = {i['name'] for i in insp.get_indexes('classes')}
    if 'join_code' in existing_indexes:
        op.drop_index('join_code', table_name='classes')
    if 'ix_classes_join_code' not in existing_indexes:
        op.create_index(op.f('ix_classes_join_code'), 'classes', ['join_code'], unique=True)
    if 'ix_classes_teacher_id' not in existing_indexes:
        op.create_index(op.f('ix_classes_teacher_id'), 'classes', ['teacher_id'], unique=False)

    op.alter_column('user_settings', 'use_websocket',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True,
               existing_server_default=sa.text("'0'"))


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user_settings', 'use_websocket',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False,
               existing_server_default=sa.text("'0'"))
    op.drop_index(op.f('ix_classes_teacher_id'), table_name='classes')
    op.drop_index(op.f('ix_classes_join_code'), table_name='classes')
    op.create_index(op.f('join_code'), 'classes', ['join_code'], unique=True)
    op.drop_index(op.f('ix_xp_transactions_user_id'), table_name='xp_transactions')
    op.drop_index(op.f('ix_xp_transactions_id'), table_name='xp_transactions')
    op.drop_table('xp_transactions')
    op.drop_table('user_gamification')
    op.drop_index(op.f('ix_user_achievements_user_id'), table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_id'), table_name='user_achievements')
    op.drop_table('user_achievements')
    # ### end Alembic commands ###
