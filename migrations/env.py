"""Ambiente Alembic com conexão injetável para testes isolados."""

import os
from pathlib import Path

from dotenv import load_dotenv

from alembic import context
from sqlalchemy import create_engine

from app.models import Base

config = context.config
target_metadata = Base.metadata


def run_migrations_online() -> None:
    supplied = config.attributes.get("connection")
    if supplied is not None:
        context.configure(connection=supplied, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        return
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Configure DATABASE_URL para executar migrações.")
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations_online()
