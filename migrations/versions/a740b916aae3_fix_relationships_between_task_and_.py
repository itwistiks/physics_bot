"""Fix relationships between Task and Theory

Revision ID: a740b916aae3
Revises: 02dc0f20e0f7
Create Date: 2025-07-26 20:05:00.161769

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a740b916aae3'
down_revision: Union[str, Sequence[str], None] = '02dc0f20e0f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('theories', sa.Column('task_id', sa.Integer(), nullable=True))
    op.create_unique_constraint(None, 'theories', ['task_id'])
    op.create_foreign_key(None, 'theories', 'tasks', ['task_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'theories', type_='foreignkey')
    op.drop_constraint(None, 'theories', type_='unique')
    op.drop_column('theories', 'task_id')
    # ### end Alembic commands ###
