"""Importa os quatro exemplos sintéticos, reutilizando FHIR salvo. Zero chamadas Google.

Uso: python scripts/import_demo_documents.py
Não altera o ledger nem substitui documentos existentes. Execute migrações/seed antes.
"""
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=False)
from sqlalchemy import select
from app.db import _session_factory
from app.exports import imaging_bundle, IMAGE_NOTICE
from app.fhir import normalize_bundle_ids, validate_bundle
from app.models import Document, User


def import_examples(db, storage_root=None):
    owner = db.scalar(select(User).where(User.email == "demo1@sauva.example"))
    if not owner:
        raise ValueError("Execute python -m app.seed antes de importar os exemplos.")
    storage = Path(storage_root) if storage_root else ROOT / "uploads"
    count = 0
    for filename in ("example_text.pdf", "example_text-1.jpeg", "example_text-2.jpeg", "example_imaging.jpeg"):
        ident = uuid5(owner.id, "sauva-demo:" + filename)
        if db.get(Document, ident):
            print(filename + ": já importado; preservado.")
            continue
        source = ROOT / "demo-files" / filename
        if not source.is_file():
            print(filename + ": original ausente; ignorado.")
            continue
        is_image = filename == "example_imaging.jpeg"
        fmt = "pdf" if source.suffix == ".pdf" else "jpg"
        if is_image:
            text = IMAGE_NOTICE
            payload = imaging_bundle(source.read_bytes(), fmt, ident, filename)
        else:
            saved = ROOT / "demo-results/gemini-only-normalized" / (filename + ".fhir.json")
            if not saved.is_file():
                print(filename + ": FHIR salvo ausente; ignorado sem chamada de IA.")
                continue
            payload = json.loads(saved.read_text(encoding="utf8"))
            transcription = ROOT / "demo-results/gemini-only" / (filename + ".extracted.txt")
            text = transcription.read_text(encoding="utf8") if transcription.is_file() else ""
        payload = validate_bundle(normalize_bundle_ids(payload, namespace=ident))
        target = storage.resolve() / str(owner.id) / f"{ident}.{fmt}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        db.add(Document(id=ident, user_id=owner.id, name="Demonstração — " + filename,
                        original_name=filename, document_type="Exame de imagem" if is_image else "Texto",
                        file_format=fmt, storage_path=str(target), status="ready", stage="completed",
                        extracted_text=text, extracted_at=datetime.now(timezone.utc),
                        fhir_payload=payload, validation_level="structural"))
        db.commit()
        count += 1
        print(filename + ": importado de resultado salvo; sem nova conversão.")
    return count


def main():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Configure DATABASE_URL localmente.")
        return 1
    try:
        with _session_factory(url)() as db:
            count = import_examples(db)
        print(f"Concluído: {count} novos documentos. Ledger preservado. Nenhuma chamada Google.")
        return 0
    except Exception as exc:
        # Never print DSNs, passwords, provider responses or clinical contents.
        print(f"Importação não concluída ({type(exc).__name__}). Confira migrações, contas e arquivos locais.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
