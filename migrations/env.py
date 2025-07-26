import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from alembic import context
from core.database.models import Base

load_dotenv()

config = context.config
target_metadata = Base.metadata


def run_migrations_online():
    connectable = create_engine(os.getenv('DB_FULL_URL'))

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
