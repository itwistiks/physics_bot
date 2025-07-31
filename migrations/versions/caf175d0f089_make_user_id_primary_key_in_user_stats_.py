"""make_user_id_primary_key_in_user_stats_v2

Revision ID: caf175d0f089
Revises: ca44a80f8d55
Create Date: 2025-07-28 15:56:29.651962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'caf175d0f089'
down_revision: Union[str, Sequence[str], None] = 'ca44a80f8d55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Проверяем существование внешнего ключа перед удалением
    inspector = inspect(op.get_bind())
    fks = inspector.get_foreign_keys('user_stats')
    fk_name = None
    for fk in fks:
        if fk['referred_table'] == 'users':
            fk_name = fk['name']
            break

    if fk_name:
        op.drop_constraint(fk_name, 'user_stats', type_='foreignkey')

    # 2. Удаляем старый первичный ключ (если существует)
    try:
        op.drop_constraint('PRIMARY', 'user_stats', type_='primary')
    except:
        pass  # Игнорируем, если PK уже удалён

    # 3. Делаем user_id первичным ключом
    op.execute("""
        ALTER TABLE user_stats 
        MODIFY COLUMN user_id INT NOT NULL,
        ADD PRIMARY KEY (user_id)
    """)

    # 4. Возвращаем внешний ключ с CASCADE
    op.create_foreign_key(
        'fk_user_stats_user_id',
        'user_stats', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # 1. Удаляем новый внешний ключ
    op.drop_constraint('fk_user_stats_user_id',
                       'user_stats', type_='foreignkey')

    # 2. Убираем PK с user_id (если нужно вернуть предыдущее состояние)
    op.execute("ALTER TABLE user_stats DROP PRIMARY KEY")

    # 3. Возвращаем старый внешний ключ (если был)
    op.create_foreign_key(
        'user_stats_ibfk_1',
        'user_stats', 'users',
        ['user_id'], ['id'],
        ondelete='RESTRICT'
    )
