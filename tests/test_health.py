"""Contrato da tarefa 01. Loopback permitido para o asyncio no Windows.

Este teste bloqueia conexões TCP remotas, não conexões a serviços locais.
Ele verifica inicialização sem configuração de credenciais/banco; não prova
isolamento de um PostgreSQL local nem substitui os testes futuros de adaptadores.
"""
import ipaddress
import socket

from fastapi.testclient import TestClient


def _is_loopback(address):
    if not isinstance(address, tuple) or not address:
        return False
    host = address[0]
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except (ValueError, TypeError):
        return False


def test_health_starts_without_service_configuration_or_remote_tcp(monkeypatch):
    for name in (
        "GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_MODEL",
        "GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "DATABASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_create_connection = socket.create_connection

    def check_address(address, family=None):
        if (family is not None and family == getattr(socket, "AF_UNIX", None)) or _is_loopback(address):
            return
        raise AssertionError("A fundação não deve abrir conexões TCP remotas")

    def guarded_connect(sock, address):
        check_address(address, sock.family)
        return original_connect(sock, address)

    def guarded_connect_ex(sock, address):
        check_address(address, sock.family)
        return original_connect_ex(sock, address)

    def guarded_create_connection(address, *args, **kwargs):
        check_address(address)
        return original_create_connection(address, *args, **kwargs)

    monkeypatch.setattr(socket, "create_connection", guarded_create_connection)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)

    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
