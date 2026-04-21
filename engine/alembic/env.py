from logging.config import fileConfig
from os import environ as env

from sqlalchemy import create_engine, pool, text

from alembic import context

import pgvector.sqlalchemy  # noqa: F401 — ensures pgvector types are importable in generated migrations

from vinculante.domain.base import Base
import vinculante.domain.entities  # noqa: F401 — ensures all models are registered on Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DB_URL = env.get("DB_URL", "postgresql+psycopg2://vinculante:vinculante@postgres/vinculante")


def run_migrations_offline() -> None:
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(DB_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.commit()

        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
