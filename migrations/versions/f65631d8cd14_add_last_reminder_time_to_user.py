"""add last_reminder_time to User

Revision ID: f65631d8cd14
Revises: 04e51e87a6d0
Create Date: 2025-08-01 17:26:58.105961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'f65631d8cd14'
down_revision: Union[str, Sequence[str], None] = '04e51e87a6d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('users', sa.Column(
        'last_reminder_time', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('users', 'last_reminder_time')
