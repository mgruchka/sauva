"""Contrato de fundação definido pelo orquestrador; executar após tarefa 01."""
import socket

from fastapi.testclient import TestClient


def test_health_starts_without_credentials_database_or_outbound_network(monkeypatch):
    for name in (
        "GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_MODEL",
        "GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "DATABASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    def reject_network(*args, **kwargs):
        raise AssertionError("A fundação não deve abrir conexões externas")

    monkeypatch.setattr(socket, "create_connection", reject_network)
    monkeypatch.setattr(socket.socket, "connect", reject_network)

    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
