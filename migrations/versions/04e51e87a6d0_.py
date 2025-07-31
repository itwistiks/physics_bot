"""

Revision ID: 04e51e87a6d0
Revises: 2ee92e40113e
Create Date: 2025-07-31 16:11:41.003845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '04e51e87a6d0'
down_revision: Union[str, Sequence[str], None] = '2ee92e40113e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Для MySQL/MariaDB
    op.alter_column('achievements', 'condition',
                    new_column_name='conditions',
                    existing_type=sa.Text(),
                    existing_nullable=True)

    # Для PostgreSQL можно использовать:
    # op.execute('ALTER TABLE achievements RENAME COLUMN condition TO conditions')


def downgrade():
    # Возвращаем обратно
    op.alter_column('achievements', 'conditions',
                    new_column_name='condition',
                    existing_type=sa.Text(),
                    existing_nullable=True)
