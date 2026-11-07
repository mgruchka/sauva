"""Aplicação executável sem serviços externos."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    application = FastAPI(title="SAÚVA")

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
