import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.model import Base  # target_metadata
import app.model  # noqa: F401  ensures models are registered
from dotenv import load_dotenv

load_dotenv()


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set for Alembic")
    return url


def run_migrations_online() -> None:
    connectable = create_engine(get_url(), pool_pre_ping=True)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
