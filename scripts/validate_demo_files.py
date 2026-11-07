"""Valida uma vez os três exemplos Texto já fornecidos por Marcos.

APIs reais; execução direta sem agente. Um arquivo é marcado antes da chamada,
para que repetir o comando não repita cobranças automaticamente.
"""
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    load_dotenv(ROOT / ".env", override=False)
    missing = [name for name in ("GEMINI_API_KEY", "GEMINI_MODEL") if not os.getenv(name)]
    if missing:
        print("Configuração ausente:", ", ".join(missing))
        return 2
    # O pedido de Marcos autoriza somente estes exemplos com os prompts atuais.
    # Ativação restrita a este processo; não reescreve .env nem libera o servidor.
    os.environ["ENABLE_REAL_GOOGLE"] = "true"
    os.environ["FHIR_PROMPT_APPROVED"] = "true"
    from app.conversion import gemini_convert, vision_ocr
    from app.extraction import extract, normalize_jpeg, pdf_pages
    from app.fhir import validate_bundle
    from pypdf import PdfReader
    from io import BytesIO

    output = ROOT / "generated" / "demo-validation"
    output.mkdir(parents=True, exist_ok=True)
    ledger_path = output / "report.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {
        "scope": "Exemplos fornecidos por Marcos; validação estrutural e APIs reais",
        "files": {},
    }
    ledger["files"]["example_imaging.jpeg"] = {
        "status": "not_implemented",
        "reason": "Pipeline Exame de imagem não implementado; radiografia não enviada para interpretação.",
    }
    names = ("example_text.pdf", "example_text-1.jpeg", "example_text-2.jpeg")
    for name in names:
        if name in ledger["files"]:
            print(name + ": já registrado; sem repetir chamadas. Consulte report.json.")
            continue
        path = ROOT / "demo-files" / name
        if not path.is_file():
            print("Arquivo ausente:", name)
            return 2
        data = path.read_bytes()
        if len(data) > 10_000_000:
            print(name + ": acima de 10 MB; nenhuma chamada.")
            return 2
        fmt = "pdf" if path.suffix.lower() == ".pdf" else "jpg"
        if fmt == "pdf":
            count = pdf_pages(data)
            reader = PdfReader(BytesIO(data))
            expected_ocr = sum(not (page.extract_text() or "").strip() for page in reader.pages)
        else:
            normalize_jpeg(data)
            count, expected_ocr = 1, 1
        entry = {
            "status": "started",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "pages": count, "vision_attempts": 0,
            "vision_budget": expected_ocr, "gemini_calls_max": 0,
        }
        ledger["files"][name] = entry
        save(ledger_path, ledger)

        def limited_ocr(content):
            if entry["vision_attempts"] >= expected_ocr:
                raise RuntimeError("Orçamento OCR esgotado.")
            entry["vision_attempts"] += 1
            save(ledger_path, ledger)
            return vision_ocr(content)

        try:
            text = extract(data, fmt, limited_ocr)
            (output / (name + ".extracted.txt")).write_text(text, encoding="utf-8")
            entry["extracted_chars"] = len(text)
            entry["gemini_calls_max"] = 2
            save(ledger_path, ledger)
            payload = validate_bundle(gemini_convert(text))
            target = output / (name + ".fhir.json")
            save(target, payload)
            entry["status"] = "ready"
            entry["validation_level"] = "structural"
            entry["resources"] = dict(Counter(
                item["resource"]["resourceType"] for item in payload["entry"]
            ))
            entry["output"] = target.name
            print(name + ": JSON gerado; conferir fidelidade ao original.")
        except Exception as error:
            entry["status"] = "error"
            entry["error_type"] = type(error).__name__
            # Não serializar resposta Google, stack com credenciais ou texto clínico.
            code = getattr(error, "code", None)
            if isinstance(code, (int, str)):
                entry["provider_code"] = code
            print(name + ": falhou (" + type(error).__name__ + "); sem retry.")
            save(ledger_path, ledger)
            print("Interrompido para diagnóstico antes de gastar com os próximos arquivos.")
            return 1
        finally:
            save(ledger_path, ledger)
    save(ledger_path, ledger)
    print("Resultados locais: generated/demo-validation/")
    print("Não equivale a teste de upload/UI/PostgreSQL nem validação completa BR Core.")
    print("example_imaging.jpeg: pipeline pendente, não aprovado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
