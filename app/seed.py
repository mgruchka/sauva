"""Criação explícita e idempotente das contas de demonstração."""

import os

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import _session_factory
from app.models import User
from app.security import hash_password


def seed_demo_accounts(db: Session, *, owner_password: str, recipient_password: str) -> None:
    for email, password in (
        ("demo1@sauva.example", owner_password),
        ("demo2@sauva.example", recipient_password),
    ):
        if not db.scalar(select(User).where(User.email == email)):
            db.add(User(email=email, password_hash=hash_password(password)))
    db.commit()


def main() -> None:
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    owner = os.getenv("DEMO_OWNER_PASSWORD")
    recipient = os.getenv("DEMO_RECIPIENT_PASSWORD")
    if not url or not owner or not recipient:
        raise SystemExit("Configure DATABASE_URL e as duas senhas DEMO_* antes do seed.")
    with _session_factory(url)() as db:
        seed_demo_accounts(db, owner_password=owner, recipient_password=recipient)
    print("Contas de demonstração prontas.")


if __name__ == "__main__":
    main()
