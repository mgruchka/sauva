"""Rotas e processamento serial de documentos de texto."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import COOKIE
from app.conversion import gemini_convert, gemini_convert_file
from app.db import _session_factory, get_db
from app.extraction import extract, normalize_jpeg, pdf_pages
from app.fhir import validate_bundle, normalize_bundle_ids
from app.models import AuthSession, Document, User
from app.security import token_digest
from app.exports import imaging_bundle, IMAGE_NOTICE

MAX_SIZE = 10_000_000


class Rename(BaseModel):
    name: str


def router_for(storage_dir: Path, allowed_origin: str | None, ocr, converter, jobs_inline: bool) -> APIRouter:
    router = APIRouter(prefix="/documents")
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sauva-document") if not jobs_inline else None
    use_gemini_file = ocr is None and converter is None
    converter = converter or gemini_convert
    root = storage_dir.resolve()

    def check_origin(request: Request):
        if not allowed_origin or request.headers.get("origin") != allowed_origin:
            raise HTTPException(403, "Origem não permitida.")

    def user(request: Request, db: Session = Depends(get_db)) -> User:
        token = request.cookies.get(COOKIE)
        row = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_digest(token))) if token else None
        if not row or row.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(401, "Sessão inválida ou expirada.")
        return row.user

    def metadata(doc: Document) -> dict:
        return {"id": str(doc.id), "name": doc.name, "status": doc.status, "stage": doc.stage,
                "error": doc.error, "created_at": doc.created_at.isoformat(),
                "document_type": doc.document_type, "folder_id": str(doc.folder_id) if doc.folder_id else None,
                "validation_level": doc.validation_level}

    def owned(db: Session, ident: UUID, owner: User) -> Document:
        doc = db.scalar(select(Document).where(Document.id == ident, Document.user_id == owner.id))
        if doc is None:
            raise HTTPException(404, "Documento não encontrado.")
        return doc

    def process(db: Session, ident: UUID):
        doc = db.get(Document, ident)
        if not doc:
            return
        try:
            doc.status, doc.stage = "processing", "extracting"
            db.commit()
            data = Path(doc.storage_path).read_bytes()
            if doc.document_type == "Exame de imagem":
                extracted = IMAGE_NOTICE
                payload = imaging_bundle(data, doc.file_format, doc.id, doc.name)
            elif use_gemini_file:
                doc.stage = "converting"
                db.commit()
                extracted, payload = gemini_convert_file(data, doc.file_format)
            else:
                # Adaptadores injetados: mantém os contratos dos testes sem API real.
                extracted = extract(data, doc.file_format, ocr)
                if not extracted.strip():
                    raise ValueError("Não foi possível extrair texto.")
                doc.stage = "converting"
                db.commit()
                payload = converter(extracted)
            doc.extracted_text = extracted
            doc.extracted_at = datetime.now(timezone.utc)
            db.commit()
            payload = validate_bundle(normalize_bundle_ids(payload, namespace=doc.id))
            doc.fhir_payload = payload
            doc.validation_level = "structural"
            doc.status, doc.stage = "ready", "completed"
            db.commit()
        except Exception:
            db.rollback()
            doc = db.get(Document, ident)
            doc.status, doc.stage = "error", "failed"
            doc.error = "Não foi possível processar o documento. Verifique o arquivo ou a configuração dos serviços."
            db.commit()

    def background(url: str, ident: UUID):
        with _session_factory(url)() as db:
            process(db, ident)

    @router.post("", status_code=202, dependencies=[Depends(check_origin)])
    async def upload(request: Request, file: UploadFile = File(...), document_type: str = Form(...), name: str | None = Form(None),
                     db: Session = Depends(get_db), owner: User = Depends(user)):
        if document_type not in {"Texto", "Exame de imagem"}:
            raise HTTPException(422, "Escolha Texto ou Exame de imagem.")
        original = file.filename or ""
        extension = Path(original).suffix.lower()
        if extension not in {".pdf", ".jpg", ".jpeg"}:
            raise HTTPException(415, "Formato não aceito. Envie PDF ou JPEG.")
        if file.content_type not in ({"application/pdf"} if extension == ".pdf" else {"image/jpeg"}):
            raise HTTPException(415, "Tipo de arquivo incompatível com a extensão.")
        chunks, total = [], 0
        while chunk := await file.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_SIZE:
                raise HTTPException(413, "Arquivo acima de 10 MB.")
            chunks.append(chunk)
        data = b"".join(chunks)
        fmt = "pdf" if extension == ".pdf" else "jpg"
        try:
            if fmt == "pdf":
                if not data.startswith(b"%PDF-"):
                    raise ValueError("PDF inválido.")
                pdf_pages(data)
            else:
                normalize_jpeg(data)
        except Exception:
            raise HTTPException(422, "Arquivo inválido, protegido ou acima de 10 páginas.") from None
        title = (name or Path(original).name).strip()
        if not title or len(title) > 255:
            raise HTTPException(422, "Nome inválido.")
        ident = uuid4()
        target = (root / str(owner.id) / f"{ident}.{fmt}").resolve()
        if not target.is_relative_to(root):
            raise HTTPException(422, "Caminho inválido.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        doc = Document(id=ident, user_id=owner.id, name=title, original_name=Path(original).name[:255],
                       document_type=document_type, file_format=fmt, storage_path=str(target), status="queued", stage="queued")
        try:
            db.add(doc)
            db.commit()
        except Exception:
            target.unlink(missing_ok=True)
            raise
        if jobs_inline:
            process(db, ident)
        else:
            url = getattr(request.app.state, "database_url", None)
            if url is None:
                import os
                url = os.environ["DATABASE_URL"]
            executor.submit(background, url, ident)
        return {"id": str(ident), "status": "queued"}

    @router.get("")
    def list_documents(db: Session = Depends(get_db), owner: User = Depends(user)):
        rows = db.scalars(select(Document).where(Document.user_id == owner.id).order_by(Document.created_at.desc())).all()
        return [metadata(row) for row in rows]

    @router.get("/{ident}")
    def get_document(ident: UUID, db: Session = Depends(get_db), owner: User = Depends(user)):
        return metadata(owned(db, ident, owner))

    @router.patch("/{ident}", dependencies=[Depends(check_origin)])
    def rename(ident: UUID, update: Rename, db: Session = Depends(get_db), owner: User = Depends(user)):
        doc = owned(db, ident, owner)
        title = update.name.strip()
        if not title or len(title) > 255:
            raise HTTPException(422, "Nome inválido.")
        doc.name = title
        db.commit()
        return metadata(doc)

    @router.get("/{ident}/json")
    def download(ident: UUID, db: Session = Depends(get_db), owner: User = Depends(user)):
        doc = owned(db, ident, owner)
        if doc.status != "ready" or not doc.fhir_payload:
            raise HTTPException(409, "JSON ainda não disponível.")
        return Response(json.dumps(doc.fhir_payload, ensure_ascii=False), media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="{ident}.json"'})

    return router
