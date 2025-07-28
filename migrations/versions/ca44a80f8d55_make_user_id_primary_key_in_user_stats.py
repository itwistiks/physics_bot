"""make_user_id_primary_key_in_user_stats

Revision ID: ca44a80f8d55
Revises: b404ced829e4
Create Date: 2025-07-28 15:47:57.614815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = 'ca44a80f8d55'
down_revision: Union[str, Sequence[str], None] = 'b404ced829e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Удаляем внешний ключ (если он есть)
    op.drop_constraint('user_stats_ibfk_1', 'user_stats', type_='foreignkey')

    # 2. Удаляем автоинкрементный id (если он есть)
    op.drop_column('user_stats', 'id')

    # 3. Делаем user_id первичным ключом
    op.alter_column('user_stats', 'user_id',
                    existing_type=sa.Integer(),
                    nullable=False,
                    primary_key=True)

    # 4. Возвращаем внешний ключ с каскадным удалением
    op.create_foreign_key(
        'fk_user_stats_user_id',
        'user_stats', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # 1. Удаляем внешний ключ
    op.drop_constraint('fk_user_stats_user_id',
                       'user_stats', type_='foreignkey')

    # 2. Возвращаем старую структуру
    op.add_column('user_stats',
                  sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False))

    # 3. Убираем PK с user_id
    op.alter_column('user_stats', 'user_id',
                    existing_type=sa.Integer(),
                    nullable=True)

    # 4. Восстанавливаем старый внешний ключ
    op.create_foreign_key(
        'user_stats_ibfk_1',
        'user_stats', 'users',
        ['user_id'], ['id'],
        ondelete='RESTRICT'
    )
