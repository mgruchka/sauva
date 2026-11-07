"""Dependências de acesso compartilhadas pelas funções do protótipo."""
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth import COOKIE
from app.db import get_db
from app.models import AuthSession, Document, User
from app.security import token_digest


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE)
    row = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_digest(token))) if token else None
    if not row or row.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(401, "Sessão inválida ou expirada.")
    return row.user


def owned_document(db, ident, owner):
    doc = db.scalar(select(Document).where(Document.id == ident, Document.user_id == owner.id))
    if doc is None:
        raise HTTPException(404, "Documento não encontrado.")
    return doc
