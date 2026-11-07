"""Pastas, exportações e resgate único para o protótipo local."""
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.access import current_user, owned_document
from app.db import get_db
from app.exports import render_pdf
from app.models import Document, Folder, ShareLink, User
from app.security import hash_password, verify_password, new_token, token_digest


class FolderName(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class Move(BaseModel):
    folder_id: UUID | None = None


class Recipient(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class Redeem(BaseModel):
    token: str = Field(min_length=20, max_length=100)
    password: str = Field(min_length=1, max_length=128)


def export_response(doc, kind):
    private = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
    if kind == "original":
        if not Path(doc.storage_path).is_file():
            raise HTTPException(404, "Arquivo original indisponível.")
        return FileResponse(doc.storage_path, media_type="application/pdf" if doc.file_format == "pdf" else "image/jpeg",
                            filename=f"{doc.id}.{doc.file_format}", content_disposition_type="inline", headers=private)
    if doc.status != "ready" or not doc.fhir_payload:
        raise HTTPException(409, "Documento ainda não está pronto.")
    if kind == "json":
        return Response(json.dumps(doc.fhir_payload, ensure_ascii=False), media_type="application/json",
                        headers={**private, "Content-Disposition": f'attachment; filename="{doc.id}.json"'})
    if kind == "pdf":
        try:
            data = render_pdf(doc)
        except Exception:
            raise HTTPException(503, "PDF indisponível. Você ainda pode abrir o original ou baixar o JSON.") from None
        return Response(data, media_type="application/pdf",
                        headers={**private, "Content-Disposition": f'inline; filename="{doc.id}.pdf"'})
    raise HTTPException(404, "Formato não encontrado.")


def router_for(allowed_origin):
    router = APIRouter()

    def origin(request: Request):
        if not allowed_origin or request.headers.get("origin") != allowed_origin:
            raise HTTPException(403, "Origem não permitida.")

    def folder_owned(db, ident, owner):
        folder = db.scalar(select(Folder).where(Folder.id == ident, Folder.user_id == owner.id))
        if folder is None:
            raise HTTPException(404, "Pasta não encontrada.")
        return folder

    @router.get("/folders")
    def folders(db: Session = Depends(get_db), owner: User = Depends(current_user)):
        return [{"id": str(f.id), "name": f.name} for f in db.scalars(select(Folder).where(Folder.user_id == owner.id).order_by(Folder.name)).all()]

    @router.post("/folders", status_code=201, dependencies=[Depends(origin)])
    def create_folder(body: FolderName, db: Session = Depends(get_db), owner: User = Depends(current_user)):
        name = body.name.strip()
        if not name:
            raise HTTPException(422, "Informe o nome da pasta.")
        folder = Folder(user_id=owner.id, name=name)
        db.add(folder)
        db.commit()
        return {"id": str(folder.id), "name": folder.name}

    @router.patch("/documents/{ident}/folder", dependencies=[Depends(origin)])
    def move(ident: UUID, body: Move, db: Session = Depends(get_db), owner: User = Depends(current_user)):
        doc = owned_document(db, ident, owner)
        if body.folder_id is not None:
            folder_owned(db, body.folder_id, owner)
        doc.folder_id = body.folder_id
        db.commit()
        return {"id": str(doc.id), "folder_id": str(doc.folder_id) if doc.folder_id else None}

    @router.get("/documents/{ident}/pdf")
    def pdf(ident: UUID, db: Session = Depends(get_db), owner: User = Depends(current_user)):
        return export_response(owned_document(db, ident, owner), "pdf")

    @router.get("/documents/{ident}/original")
    def original(ident: UUID, db: Session = Depends(get_db), owner: User = Depends(current_user)):
        return export_response(owned_document(db, ident, owner), "original")

    @router.post("/documents/{ident}/shares", status_code=201, dependencies=[Depends(origin)])
    def share(ident: UUID, body: Recipient, db: Session = Depends(get_db), owner: User = Depends(current_user)):
        doc = owned_document(db, ident, owner)
        if doc.status != "ready":
            raise HTTPException(409, "Aguarde o processamento do documento.")
        recipient = db.scalar(select(User).where(User.email == body.email.strip().lower()))
        if recipient is None or recipient.id == owner.id:
            raise HTTPException(422, "Escolha outra conta de demonstração cadastrada.")
        token, password = new_token(), f"{secrets.randbelow(1000000):06d}"
        row = ShareLink(document_id=doc.id, recipient_id=recipient.id, token_hash=token_digest(token),
                        password_hash=hash_password(password), expires_at=datetime.now(timezone.utc) + timedelta(hours=24))
        db.add(row)
        db.commit()
        return {"url": "/#share=" + token, "password": password, "expires_at": row.expires_at.isoformat()}

    @router.post("/shares/redeem", dependencies=[Depends(origin)])
    def redeem(body: Redeem, db: Session = Depends(get_db), owner: User = Depends(current_user)):
        # Row lock serializes simultaneous redemptions and failed-attempt updates.
        row = db.scalar(select(ShareLink).where(ShareLink.token_hash == token_digest(body.token)).with_for_update())
        now = datetime.now(timezone.utc)
        if not row or row.recipient_id != owner.id:
            raise HTTPException(404, "Compartilhamento não encontrado para esta conta.")
        if row.redeemed_at or row.expires_at <= now or row.failed_attempts >= 5:
            raise HTTPException(410, "Link utilizado, expirado ou bloqueado.")
        if not verify_password(body.password, row.password_hash):
            row.failed_attempts += 1
            db.commit()
            raise HTTPException(403, "Senha inválida.")
        grant = new_token()
        row.redeemed_at, row.grant_hash = now, token_digest(grant)
        row.access_expires_at = now + timedelta(minutes=10)
        db.commit()
        doc = db.get(Document, row.document_id)
        return {"grant": grant, "name": doc.name, "expires_at": row.access_expires_at.isoformat()}

    @router.get("/shared/{grant}/{kind}")
    def shared(grant: str, kind: str, db: Session = Depends(get_db), owner: User = Depends(current_user)):
        row = db.scalar(select(ShareLink).where(ShareLink.grant_hash == token_digest(grant), ShareLink.recipient_id == owner.id))
        if not row or not row.access_expires_at or row.access_expires_at <= datetime.now(timezone.utc):
            raise HTTPException(410, "Acesso encerrado ou indisponível.")
        doc = db.get(Document, row.document_id)
        if doc is None:
            raise HTTPException(404, "Documento indisponível.")
        return export_response(doc, kind)

    return router
