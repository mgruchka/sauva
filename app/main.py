"""Aplicação executável sem serviços externos."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.auth import router_for
from app.documents import router_for as documents_router
from app.features import router_for as features_router


def create_app(*, database_url: str | None = None, allowed_origin: str | None = None, cookie_secure: bool | None = None,
               storage_dir=None, ocr=None, converter=None, jobs_inline: bool = False) -> FastAPI:
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
    application.include_router(documents_router(Path(storage_dir) if storage_dir is not None else Path("uploads"), origin, ocr, converter, jobs_inline))
    application.include_router(features_router(origin))
    web = Path(__file__).resolve().parents[1] / "web"
    application.mount("/assets", StaticFiles(directory=web), name="assets")

    @application.middleware("http")
    async def privacy_headers(request, call_next):
        response = await call_next(request)
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        if not request.url.path.startswith("/assets/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.get("/", include_in_schema=False)
    def home():
        return FileResponse(web / "index.html")

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
