import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool
from alembic import context
from core.database.models import Base

load_dotenv()

config = context.config
target_metadata = Base.metadata


def get_url():
    """Получает URL из переменных окружения или config"""
    return os.getenv('DB_FULL_URL') or config.get_main_option("sqlalchemy.url")


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        get_url(),
        poolclass=pool.NullPool  # Важно для миграций
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    print("Миграции в офлайн-режиме не поддерживаются")
else:
    run_migrations_online()
