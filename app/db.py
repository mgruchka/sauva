"""Sessões PostgreSQL abertas somente quando uma rota precisa delas."""

import os
from functools import lru_cache

from fastapi import HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@lru_cache(maxsize=8)
def _session_factory(url: str):
    return sessionmaker(bind=create_engine(url), expire_on_commit=False)


def get_db(request: Request):
    url = getattr(request.app.state, "database_url", None) or os.getenv("DATABASE_URL")
    if not url:
        raise HTTPException(status_code=503, detail="Banco de dados não configurado.")
    with _session_factory(url)() as db:
        yield db
