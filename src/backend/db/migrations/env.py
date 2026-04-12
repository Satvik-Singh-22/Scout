"""
Banquoite — Alembic Migration Environment

Configures Alembic to use:
  - DATABASE_URL from environment (sync version for migrations)
  - All SQLAlchemy models via Base.metadata for autogenerate
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv()

# Import all models so Alembic can detect them for autogenerate
from backend.db.models import Base  # noqa: E402

# Alembic Config object
config = context.config

# Override sqlalchemy.url with the sync version of DATABASE_URL
database_url = os.getenv("DATABASE_URL", "")
if database_url:
    # Alembic requires a sync driver — convert asyncpg to psycopg2
    sync_url = database_url.replace("+asyncpg", "+psycopg2")
    # psycopg2 uses sslmode=require, not ssl=require
    sync_url = sync_url.replace("ssl=require", "sslmode=require")
    config.set_main_option("sqlalchemy.url", sync_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL scripts without requiring a live database connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates an engine and associates a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
