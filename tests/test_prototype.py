"""Três testes focados: exportação, pastas/imagem e ciclo do compartilhamento."""
import json
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

from pypdf import PdfReader
from sqlalchemy import select
from tests.test_auth import auth_engine, auth_db, seeded_db  # noqa: F401
from tests.test_auth import ORIGIN, EMAIL_1, EMAIL_2, PASSWORD_1, PASSWORD_2
from tests.test_documents import flow, make_jpeg, make_pdf, upload, document  # noqa: F401


def test_saved_fhir_pdf_exports_and_image_attachment(tmp_path):
    from app.exports import render_pdf, imaging_bundle
    from app.fhir import validate_bundle
    root = Path(__file__).resolve().parents[1]
    saved = list((root / "demo-results/gemini-only-normalized").glob("*.json"))
    assert len(saved) == 3
    for source in saved:
        doc = SimpleNamespace(name="Demonstração <&> " + source.name, document_type="Texto",
                              fhir_payload=validate_bundle(json.loads(source.read_text(encoding="utf8"))),
                              extracted_text="Transcrição sintética <tag> & conteúdo", file_format="pdf")
        data = render_pdf(doc)
        pages = PdfReader(BytesIO(data)).pages
        assert pages and "SAÚVA" in pages[0].extract_text()
        assert "Transcrição sintética <tag> & conteúdo" in pages[-1].extract_text()
    image = make_jpeg()
    bundle = validate_bundle(imaging_bundle(image, "jpg", uuid4(), "Imagem"))
    import base64
    assert base64.b64decode(bundle["entry"][0]["resource"]["content"][0]["attachment"]["data"]) == image
    path = tmp_path / "image.jpg"
    path.write_bytes(image)
    doc = SimpleNamespace(name="Exame", document_type="Exame de imagem", file_format="jpg", storage_path=str(path))
    pdf = PdfReader(BytesIO(render_pdf(doc)))
    assert sum(len(page.images) for page in pdf.pages) == 1
    source_pdf = tmp_path / "image.pdf"
    source_pdf.write_bytes(make_pdf(["Original preservado"]))
    doc.file_format, doc.storage_path = "pdf", str(source_pdf)
    result = PdfReader(BytesIO(render_pdf(doc)))
    assert len(result.pages) == 2 and "Original preservado" in result.pages[-1].extract_text()


def switch(client, email, password):
    client.post("/auth/logout", headers={"Origin": ORIGIN})
    assert client.post("/auth/login", json={"email": email, "password": password}, headers={"Origin": ORIGIN}).status_code == 200


def test_image_folder_exports_and_tenant_isolation(flow):
    client, ocr, converter, storage, db = flow
    folder = client.post("/folders", json={"name": "Exames"}, headers={"Origin": ORIGIN}).json()
    response = client.post("/documents", data={"document_type": "Exame de imagem"},
                           files={"file": ("imagem.jpeg", make_jpeg(), "image/jpeg")}, headers={"Origin": ORIGIN})
    info = document(client, response)
    assert info["status"] == "ready" and not ocr.calls and not converter.calls
    path = "/documents/" + info["id"]
    assert client.patch(path + "/folder", json={"folder_id": folder["id"]}, headers={"Origin": ORIGIN}).status_code == 200
    assert client.get(path).json()["folder_id"] == folder["id"]
    assert client.get(path + "/json").json()["entry"][0]["resource"]["resourceType"] == "DocumentReference"
    pdf = client.get(path + "/pdf")
    assert pdf.status_code == 200 and PdfReader(BytesIO(pdf.content)).pages
    assert client.get(path + "/original").content == make_jpeg()
    assert client.post("/folders", json={"name": "blocked"}).status_code == 403
    switch(client, EMAIL_2, PASSWORD_2)
    assert client.get("/folders").json() == []
    assert client.get(path + "/pdf").status_code == 404
    assert client.get(path + "/original").status_code == 404
    own = document(client, upload(client, make_pdf(["Outro registro"])))
    assert client.patch("/documents/" + own["id"] + "/folder", json={"folder_id": folder["id"]}, headers={"Origin": ORIGIN}).status_code == 404
    assert client.get("/health").status_code == 200


def test_single_use_sharing_password_expiry_and_scope(flow):
    from app.models import ShareLink
    client, ocr, converter, storage, db = flow
    info = document(client, upload(client, make_pdf(["Registro sintetico"])))
    path = "/documents/" + info["id"]
    assert client.post(path + "/shares", json={"email": EMAIL_2}).status_code == 403
    invitation = client.post(path + "/shares", json={"email": EMAIL_2}, headers={"Origin": ORIGIN}).json()
    body = {"token": invitation["url"].split("share=")[1], "password": invitation["password"]}
    assert client.post("/shares/redeem", json=body, headers={"Origin": ORIGIN}).status_code == 404
    switch(client, EMAIL_2, PASSWORD_2)
    wrong = {**body, "password": "wrong"}
    assert client.post("/shares/redeem", json=wrong, headers={"Origin": ORIGIN}).status_code == 403
    redeemed = client.post("/shares/redeem", json=body, headers={"Origin": ORIGIN})
    assert redeemed.status_code == 200
    grant = redeemed.json()["grant"]
    base = "/shared/" + grant
    assert client.post("/shares/redeem", json=body, headers={"Origin": ORIGIN}).status_code == 410
    for kind in ("original", "pdf", "json"):
        result = client.get(base + "/" + kind)
        assert result.status_code == 200
        assert result.headers["cache-control"] == "no-store"
    assert client.get(path).status_code == 404
    assert client.get(base + "/unknown").status_code == 404
    switch(client, EMAIL_1, PASSWORD_1)
    assert client.get(base + "/json").status_code == 410
    switch(client, EMAIL_2, PASSWORD_2)
    row = db.scalar(select(ShareLink))
    row.access_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    assert client.get(base + "/json").status_code == 410
    switch(client, EMAIL_1, PASSWORD_1)
    other = client.post(path + "/shares", json={"email": EMAIL_2}, headers={"Origin": ORIGIN}).json()
    token = other["url"].split("share=")[1]
    from app.security import token_digest
    second = db.scalar(select(ShareLink).where(ShareLink.token_hash == token_digest(token)))
    second.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    switch(client, EMAIL_2, PASSWORD_2)
    assert client.post("/shares/redeem", json={"token": token, "password": other["password"]}, headers={"Origin": ORIGIN}).status_code == 410
    assert client.get("/health").status_code == 200
