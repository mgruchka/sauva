"""Aceite da tarefa 02. PostgreSQL real, schema exclusivo e rollback por teste.

Executar só com TEST_DATABASE_URL apontando para banco separado terminado em _test.
Não lê .env; não imprime URLs. Credenciais abaixo são fixtures sintéticas.
"""
import hashlib
import os
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

ORIGIN = "http://127.0.0.1:8000"
EMAIL_1 = "demo1@sauva.example"
EMAIL_2 = "demo2@sauva.example"
PASSWORD_1 = "Synthetic-owner-test-123!"
PASSWORD_2 = "Synthetic-recipient-test-456!"


@pytest.fixture(scope="session")
def auth_engine():
    raw = os.environ.get("TEST_DATABASE_URL")
    if not raw:
        pytest.fail("Configure TEST_DATABASE_URL para um PostgreSQL separado (_test).")
    url = make_url(raw)
    if url.drivername != "postgresql+psycopg" or not (url.database or "").endswith("_test"):
        pytest.fail("Use postgresql+psycopg e um banco cujo nome termine em _test.")
    development = os.environ.get("DATABASE_URL")
    if development and make_url(development).database == url.database:
        pytest.fail("O banco de testes deve ser diferente do banco de desenvolvimento.")
    schema = "sauva_test_" + uuid4().hex
    admin_engine = create_engine(url)
    engine = None
    created = False
    try:
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        created = True
        engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
        root = Path(__file__).resolve().parents[1]
        config = Config(str(root / "alembic.ini"))
        config.set_main_option("script_location", str(root / "migrations"))
        # env.py deve aceitar a conexão fornecida e NÃO abrir outra conexão.
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield engine
    finally:
        if engine is not None:
            engine.dispose()
        if created:
            with admin_engine.begin() as connection:
                connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()


@pytest.fixture
def auth_db(auth_engine):
    with auth_engine.connect() as connection:
        transaction = connection.begin()
        with Session(
            bind=connection, join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        ) as session:
            try:
                yield session
            finally:
                if transaction.is_active:
                    # Fecha a sessão/savepoint antes do rollback externo.
                    session.close()
                    transaction.rollback()


@pytest.fixture
def seeded_db(auth_db):
    from app.seed import seed_demo_accounts
    seed_demo_accounts(
        auth_db, owner_password=PASSWORD_1, recipient_password=PASSWORD_2,
    )
    return auth_db


@pytest.fixture
def auth_app(seeded_db):
    from app.db import get_db
    from app.main import create_app
    application = create_app(
        database_url=os.environ["TEST_DATABASE_URL"],
        allowed_origin=ORIGIN, cookie_secure=False,
    )

    def override_db():
        yield seeded_db

    application.dependency_overrides[get_db] = override_db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(auth_app):
    with TestClient(auth_app, base_url=ORIGIN) as connection:
        yield connection


def login(client, email=EMAIL_1, password=PASSWORD_1):
    return client.post(
        "/auth/login", json={"email": email, "password": password},
        headers={"Origin": ORIGIN},
    )


def test_demo_seed_is_idempotent_and_passwords_are_argon2id(auth_db):
    from app.models import User
    from app.security import verify_password
    from app.seed import seed_demo_accounts
    seed_demo_accounts(auth_db, owner_password=PASSWORD_1, recipient_password=PASSWORD_2)
    users = auth_db.scalars(select(User).order_by(User.email)).all()
    assert [user.email for user in users] == [EMAIL_1, EMAIL_2]
    original = {user.email: (user.id, user.password_hash) for user in users}
    seed_demo_accounts(
        auth_db, owner_password="Different-synthetic-password!",
        recipient_password="Another-synthetic-password!",
    )
    auth_db.expire_all()
    users = auth_db.scalars(select(User).order_by(User.email)).all()
    assert {user.email: (user.id, user.password_hash) for user in users} == original
    for user, password in zip(users, (PASSWORD_1, PASSWORD_2)):
        assert user.password_hash.startswith("$argon2id$")
        assert verify_password(password, user.password_hash)
        assert not verify_password("incorrect", user.password_hash)
        assert user.password_hash != password


def test_login_cookie_identity_token_storage_and_https(client, seeded_db):
    from app.db import get_db
    from app.main import create_app
    from app.models import AuthSession

    for email, password in ((EMAIL_1, PASSWORD_1), (EMAIL_2, PASSWORD_2)):
        client.cookies.clear()
        before = datetime.now(timezone.utc)
        response = login(client, email, password)
        assert response.status_code == 200
        identity = response.json()
        assert set(identity) == {"id", "email"}
        assert identity["email"] == email
        assert client.get("/auth/me").json() == identity
        parsed = SimpleCookie()
        parsed.load(response.headers["set-cookie"])
        cookie = parsed["sauva_session"]
        assert cookie["httponly"]
        assert cookie["samesite"].lower() == "lax"
        assert cookie["path"] == "/"
        assert int(cookie["max-age"]) == 28800
        assert not cookie["secure"]
        token = client.cookies.get("sauva_session")
        assert len(token) >= 32
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        row = seeded_db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash))
        assert row is not None
        assert str(row.user_id) == identity["id"]
        assert row.token_hash != token
        assert before + timedelta(hours=8) - timedelta(seconds=5) <= row.expires_at
        assert row.expires_at <= datetime.now(timezone.utc) + timedelta(hours=8, seconds=5)
        assert token not in response.text
        assert "password_hash" not in response.text

    https_origin = "https://127.0.0.1:8000"
    secure_app = create_app(
        database_url=os.environ["TEST_DATABASE_URL"],
        allowed_origin=https_origin, cookie_secure=True,
    )
    def override_db():
        yield seeded_db
    secure_app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(secure_app, base_url=https_origin) as secure_client:
            response = secure_client.post(
                "/auth/login", json={"email": EMAIL_1, "password": PASSWORD_1},
                headers={"Origin": https_origin},
            )
            assert response.status_code == 200
            parsed = SimpleCookie()
            parsed.load(response.headers["set-cookie"])
            assert parsed["sauva_session"]["secure"]
    finally:
        secure_app.dependency_overrides.clear()


def test_invalid_credentials_share_error_and_create_no_session(client, seeded_db):
    from app.models import AuthSession
    before = seeded_db.scalar(select(func.count()).select_from(AuthSession))
    wrong_password = login(client, password="incorrect")
    missing_user = login(client, email="missing@sauva.example")
    assert wrong_password.status_code == missing_user.status_code == 401
    assert wrong_password.json() == missing_user.json() == {
        "detail": "Email ou senha inválidos."
    }
    assert seeded_db.scalar(select(func.count()).select_from(AuthSession)) == before
    assert not client.cookies.get("sauva_session")


def test_missing_expired_and_revoked_sessions_are_rejected(client, seeded_db):
    from app.models import AuthSession
    assert client.get("/auth/me").status_code == 401
    assert login(client).status_code == 200
    token = client.cookies.get("sauva_session")
    row = seeded_db.scalar(select(AuthSession).where(
        AuthSession.token_hash == hashlib.sha256(token.encode()).hexdigest()
    ))
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    seeded_db.commit()
    assert client.get("/auth/me").status_code == 401
    client.cookies.clear()
    assert login(client).status_code == 200
    token = client.cookies.get("sauva_session")
    response = client.post("/auth/logout", headers={"Origin": ORIGIN})
    assert response.status_code == 204
    assert response.content == b""
    assert not client.cookies.get("sauva_session")
    client.cookies.set("sauva_session", token, path="/")
    assert client.get("/auth/me").status_code == 401
    client.cookies.clear()
    assert client.post("/auth/logout", headers={"Origin": ORIGIN}).status_code == 204


def test_origin_check_prevents_login_and_logout_side_effects(client, seeded_db):
    from app.models import AuthSession
    blocked = ({}, {"Origin": "null"}, {"Origin": "https://untrusted.example"},
               {"Origin": ORIGIN + ".untrusted.example"})
    for headers in blocked:
        assert client.post("/auth/login", json={
            "email": EMAIL_1, "password": PASSWORD_1,
        }, headers=headers).status_code == 403
    assert seeded_db.scalar(select(func.count()).select_from(AuthSession)) == 0
    assert login(client).status_code == 200
    for headers in blocked:
        assert client.post("/auth/logout", headers=headers).status_code == 403
        assert client.get("/auth/me").status_code == 200
    assert client.post("/auth/logout", headers={"Origin": ORIGIN}).status_code == 204
