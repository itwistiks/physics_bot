"""Add WeeklyXP model

Revision ID: 4126dd3752a9
Revises: caf175d0f089
Create Date: 2025-07-31 12:57:46.464685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '4126dd3752a9'
down_revision: Union[str, Sequence[str], None] = 'caf175d0f089'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    inspector = inspect(op.get_bind())

    # Проверяем, существует ли таблица
    if 'weekly_xp' not in inspector.get_table_names():
        op.create_table('weekly_xp',
                        sa.Column('user_id', sa.Integer(), nullable=False),
                        sa.Column('week_start_date',
                                  sa.Date(), nullable=False),
                        sa.Column('xp_earned', sa.Integer(),
                                  server_default='0'),
                        sa.PrimaryKeyConstraint('user_id', 'week_start_date'),
                        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
                        )


def downgrade():
    op.drop_table('weekly_xp')
