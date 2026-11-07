"""Rotas de autenticação demo."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuthSession, User
from app.security import new_token, token_digest, verify_password

COOKIE = "sauva_session"
MAX_AGE = 28800


class Credentials(BaseModel):
    email: str
    password: str


def router_for(allowed_origin: str | None, cookie_secure: bool) -> APIRouter:
    router = APIRouter(prefix="/auth")

    def check_origin(request: Request) -> None:
        if not allowed_origin or request.headers.get("origin") != allowed_origin:
            raise HTTPException(status_code=403, detail="Origem não permitida.")

    def current_user(request: Request, db: Session) -> User:
        token = request.cookies.get(COOKIE)
        row = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_digest(token))) if token else None
        if not row or row.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")
        return row.user

    def identity(user: User) -> dict[str, str]:
        return {"id": str(user.id), "email": user.email}

    @router.post("/login", dependencies=[Depends(check_origin)])
    def login(credentials: Credentials, response: Response, db: Session = Depends(get_db)):
        user = db.scalar(select(User).where(User.email == credentials.email.strip().lower()))
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Email ou senha inválidos.")
        token = new_token()
        db.add(AuthSession(user_id=user.id, token_hash=token_digest(token), expires_at=datetime.now(timezone.utc) + timedelta(seconds=MAX_AGE)))
        db.commit()
        response.set_cookie(COOKIE, token, max_age=MAX_AGE, httponly=True, samesite="lax", path="/", secure=cookie_secure)
        return identity(user)

    @router.get("/me")
    def me(request: Request, db: Session = Depends(get_db)):
        return identity(current_user(request, db))

    @router.post("/logout", status_code=204, dependencies=[Depends(check_origin)])
    def logout(request: Request, response: Response, db: Session = Depends(get_db)):
        token = request.cookies.get(COOKIE)
        if token:
            row = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_digest(token)))
            if row:
                db.delete(row)
                db.commit()
        response.delete_cookie(COOKIE, path="/", secure=cookie_secure, httponly=True, samesite="lax")

    return router
