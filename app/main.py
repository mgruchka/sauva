"""Aplicação executável sem serviços externos."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.auth import router_for


def create_app(*, database_url: str | None = None, allowed_origin: str | None = None, cookie_secure: bool | None = None) -> FastAPI:
    load_dotenv()
    application = FastAPI(title="SAÚVA")
    if database_url is not None:
        application.state.database_url = database_url
    origin = allowed_origin if allowed_origin is not None else os.getenv("APP_ORIGIN")
    secure = cookie_secure if cookie_secure is not None else (
        bool(origin and origin.startswith("https://"))
        or os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    )
    application.include_router(router_for(origin, secure))

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
