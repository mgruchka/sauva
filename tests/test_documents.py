"""Fluxo de texto: cinco testes de integração, Google sempre simulado."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from reportlab.pdfgen.canvas import Canvas

# Reutiliza PostgreSQL isolado e contas; não duplica setup nem altera aceite auth.
from tests.test_auth import auth_engine, auth_db, seeded_db  # noqa: F401
from tests.test_auth import ORIGIN, EMAIL_1, EMAIL_2, PASSWORD_1, PASSWORD_2


def make_pdf(pages):
    output = BytesIO()
    pdf = Canvas(output, pageCompression=0)
    for text in pages:
        if text:
            pdf.drawString(40, 750, text)
        pdf.showPage()
    pdf.save()
    return output.getvalue()


def make_jpeg():
    output = BytesIO()
    Image.new("RGB", (180, 100), "white").save(output, format="JPEG")
    return output.getvalue()


def bundle():
    patient_id, observation_id = str(uuid4()), str(uuid4())
    patient_url = "urn:uuid:" + patient_id
    return {
        "resourceType": "Bundle", "id": str(uuid4()), "type": "collection",
        "entry": [
            {"fullUrl": patient_url, "resource": {
                "resourceType": "Patient", "id": patient_id,
                "name": [{"text": "Pessoa Sintetica"}],
            }},
            {"fullUrl": "urn:uuid:" + observation_id, "resource": {
                "resourceType": "Observation", "id": observation_id,
                "status": "unknown", "code": {"text": "Temperatura"},
                "subject": {"reference": patient_url},
                "valueQuantity": {"value": 37, "unit": "C"},
            }},
        ],
    }


class FakeOCR:
    def __init__(self):
        self.calls = []
        self.fail = False

    def __call__(self, image_bytes):
        with Image.open(BytesIO(image_bytes)) as image:
            assert image.format == "JPEG"
            image.verify()
        self.calls.append(image_bytes)
        if self.fail:
            raise RuntimeError("SECRET_PROVIDER_ERROR_MUST_NOT_LEAK")
        return "Pessoa Sintetica. Temperatura 37 C. Pagina OCR."


class FakeConverter:
    def __init__(self):
        self.calls = []
        self.mode = "ok"

    def __call__(self, text):
        self.calls.append(text)
        if self.mode == "raise":
            raise RuntimeError("SECRET_PROVIDER_ERROR_MUST_NOT_LEAK")
        if self.mode == "invalid":
            return {"resourceType": "Patient"}
        result = bundle()
        if self.mode == "dangling":
            result["entry"][1]["resource"]["subject"]["reference"] = "Patient/missing"
        return deepcopy(result)


@pytest.fixture
def flow(seeded_db, tmp_path, monkeypatch):
    from app.db import get_db
    from app.main import create_app
    import os

    monkeypatch.setenv("ENABLE_REAL_GOOGLE", "false")
    ocr, converter = FakeOCR(), FakeConverter()
    storage = tmp_path / "uploads"
    application = create_app(
        database_url=os.environ["TEST_DATABASE_URL"], allowed_origin=ORIGIN,
        cookie_secure=False, storage_dir=storage, ocr=ocr, converter=converter,
        jobs_inline=True,
    )

    def override_db():
        yield seeded_db

    application.dependency_overrides[get_db] = override_db
    with TestClient(application, base_url=ORIGIN) as client:
        response = client.post("/auth/login", json={
            "email": EMAIL_1, "password": PASSWORD_1,
        }, headers={"Origin": ORIGIN})
        assert response.status_code == 200
        yield client, ocr, converter, storage, seeded_db
    application.dependency_overrides.clear()


def upload(client, content, filename="texto.pdf", mime="application/pdf"):
    return client.post("/documents", data={"document_type": "Texto"}, files={
        "file": (filename, content, mime),
    }, headers={"Origin": ORIGIN})


def document(client, response):
    assert response.status_code == 202, response.text
    doc_id = response.json()["id"]
    UUID(doc_id)
    result = client.get("/documents/" + doc_id)
    assert result.status_code == 200
    return result.json()


def test_text_pdf_roundtrip_storage_rename_and_no_reconversion(flow):
    client, ocr, converter, storage, db = flow
    text = "Pessoa Sintetica. Temperatura 37 C."
    info = document(client, upload(client, make_pdf([text]), "../../texto.pdf"))
    assert info["status"] == "ready"
    assert info["validation_level"] == "structural"
    assert len(ocr.calls) == 0 and len(converter.calls) == 1
    assert text in converter.calls[0]
    files = [p for p in storage.rglob("*") if p.is_file()]
    assert len(files) == 1
    assert files[0].resolve().is_relative_to(storage.resolve())
    assert files[0].suffix.lower() == ".pdf"
    assert files[0].stem == info["id"]
    metadata = client.get("/documents").json()
    assert [row["id"] for row in metadata] == [info["id"]]
    assert "storage_path" not in info and "extracted_text" not in info
    download = client.get("/documents/" + info["id"] + "/json")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/json")
    assert "attachment" in download.headers["content-disposition"].lower()
    assert download.json()["resourceType"] == "Bundle"
    renamed = client.patch("/documents/" + info["id"], json={"name": "Registro teste"},
                           headers={"Origin": ORIGIN})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Registro teste"
    assert client.get("/documents/" + info["id"] + "/json").json() == download.json()
    assert len(converter.calls) == 1


def test_mixed_pdf_and_jpeg_only_ocr_when_needed(flow):
    client, ocr, converter, storage, db = flow
    mixed = document(client, upload(client, make_pdf(["Pagina com texto", ""])))
    assert mixed["status"] == "ready"
    assert len(ocr.calls) == 1
    assert "Pagina com texto" in converter.calls[-1]
    assert "Pagina OCR" in converter.calls[-1]
    jpeg = document(client, upload(client, make_jpeg(), "foto.jpeg", "image/jpeg"))
    assert jpeg["status"] == "ready"
    assert len(ocr.calls) == 2 and len(converter.calls) == 2


def test_auth_origin_and_owner_isolation(flow):
    client, ocr, converter, storage, db = flow
    info = document(client, upload(client, make_pdf(["Texto sintetico"])))
    path = "/documents/" + info["id"]
    assert client.post("/auth/logout", headers={"Origin": ORIGIN}).status_code == 204
    assert upload(client, make_pdf(["Nao autenticado"])).status_code == 401
    assert client.get("/documents").status_code == 401
    assert client.post("/auth/login", json={"email": EMAIL_2, "password": PASSWORD_2},
                       headers={"Origin": ORIGIN}).status_code == 200
    assert client.get("/documents").json() == []
    assert client.get(path).status_code == 404
    assert client.get(path + "/json").status_code == 404
    assert client.patch(path, json={"name": "Intruso"},
                        headers={"Origin": ORIGIN}).status_code == 404
    assert client.get("/documents/" + str(uuid4())).status_code == 404
    for origin in (None, "null", "https://untrusted.example"):
        headers = {} if origin is None else {"Origin": origin}
        response = client.post("/documents", data={"document_type": "Texto"},
                               files={"file": ("x.pdf", make_pdf(["Teste"]), "application/pdf")},
                               headers=headers)
        assert response.status_code == 403
    assert len(converter.calls) == 1


def test_provider_errors_and_invalid_fhir_are_not_success(flow):
    client, ocr, converter, storage, db = flow
    ocr.fail = True
    info = document(client, upload(client, make_jpeg(), "x.jpg", "image/jpeg"))
    assert info["status"] == "error" and info["error"]
    assert len(converter.calls) == 0
    assert "SECRET_PROVIDER" not in str(info)
    assert client.get("/documents/" + info["id"] + "/json").status_code == 409
    ocr.fail = False
    for mode in ("raise", "invalid", "dangling"):
        converter.mode = mode
        info = document(client, upload(client, make_pdf(["Pessoa Sintetica"])))
        assert info["status"] == "error" and info["error"]
        assert "SECRET_PROVIDER" not in str(info)
        assert client.get("/documents/" + info["id"] + "/json").status_code == 409
    converter.mode = "ok"
    assert document(client, upload(client, make_pdf(["Pessoa Sintetica"])))["status"] == "ready"
    assert client.get("/health").status_code == 200


def test_upload_limits_reject_before_storage_or_provider_calls(flow):
    client, ocr, converter, storage, db = flow
    valid = make_pdf(["Texto"])
    assert upload(client, b"%PDF-" + b"x" * 10_000_000).status_code == 413
    assert upload(client, make_pdf(["Texto"] * 11)).status_code == 422
    assert upload(client, b"not a pdf").status_code == 422
    assert upload(client, valid, "x.png", "image/png").status_code == 415
    assert upload(client, b"not a jpeg", "x.jpg", "image/jpeg").status_code == 422
    assert client.get("/documents").json() == []
    assert not [p for p in storage.rglob("*") if p.is_file()]
    assert not ocr.calls and not converter.calls
