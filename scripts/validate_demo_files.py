"""Testes reais Gemini-only dos exemplos fictícios, com ledger e sem retries."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from uuid import NAMESPACE_URL, uuid5

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
NAMES = ("example_text.pdf", "example_text-1.jpeg", "example_text-2.jpeg", "example_imaging.jpeg")


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def safe_error(error):
    message = str(getattr(error, "message", None) or str(error))
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "DEMO_OWNER_PASSWORD",
                 "DEMO_RECIPIENT_PASSWORD", "DATABASE_URL", "TEST_DATABASE_URL"):
        secret = os.getenv(name)
        if secret:
            message = message.replace(secret, "[REDACTED]")
    message = re.sub(r"AIza[A-Za-z0-9_-]+", "[REDACTED]", message)
    message = re.sub(r"(?i)([?&]key=)[^\s&\"']+", r"\1[REDACTED]", message)
    return message[:1200]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", choices=NAMES, help="Executar apenas um exemplo.")
    parser.add_argument("--retry-failed", choices=NAMES,
                        help="Nova tentativa EXPLÍCITA só do arquivo falho, após corrigir a causa.")
    args = parser.parse_args()
    if args.file and args.retry_failed:
        parser.error("Escolha --file OU --retry-failed.")
    load_dotenv(ROOT / ".env", override=False)
    # Autorizado por Marcos: demos Gemini-only. Não modifica .env ou servidor.
    os.environ["ENABLE_REAL_GOOGLE"] = "true"
    os.environ["FHIR_PROMPT_APPROVED"] = "true"
    os.environ.setdefault("GEMINI_MIN_INTERVAL_SECONDS", "15")
    from app.conversion import gemini_convert_file
    from app.fhir import validate_bundle, normalize_bundle_ids
    from app.exports import imaging_bundle, IMAGE_NOTICE

    output = ROOT / "generated" / "demo-gemini"
    output.mkdir(parents=True, exist_ok=True)
    ledger_path = output / "report.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {
        "pipeline": "gemini-only-v1", "files": {}, "history": [],
    }
    # Ledger novo: preserva a tentativa Vision anterior em demo-validation/.
    previous_image = ledger["files"].get("example_imaging.jpeg")
    if previous_image and previous_image.get("status") == "not_implemented":
        ledger["history"].append({"file": "example_imaging.jpeg", **previous_image})
        del ledger["files"]["example_imaging.jpeg"]
    if args.retry_failed:
        old = ledger["files"].get(args.retry_failed)
        if not old or old.get("status") != "error":
            print("Retry permitido somente para arquivo marcado como error no ledger Gemini.")
            return 2
        ledger["history"].append({"file": args.retry_failed, **old})
        del ledger["files"][args.retry_failed]
        save(ledger_path, ledger)
    names = (args.retry_failed or args.file,) if args.retry_failed or args.file else NAMES
    failures = 0
    for name in names:
        if name in ledger["files"]:
            print(name + ": já registrado; nenhuma chamada repetida.")
            continue
        path = ROOT / "demo-files" / name
        if not path.is_file():
            print("Arquivo ausente:", name)
            failures += 1
            continue
        data = path.read_bytes()
        if not data or len(data) > 10_000_000:
            print(name + ": arquivo vazio/acima de 10 MB; nenhuma chamada.")
            failures += 1
            continue
        entry = {
            "status": "started", "started_at": datetime.now(timezone.utc).isoformat(),
            "gemini_calls_max": 0 if name == "example_imaging.jpeg" else 2, "vision_calls": 0,
        }
        ledger["files"][name] = entry
        save(ledger_path, ledger)
        try:
            fmt = "pdf" if path.suffix.lower() == ".pdf" else "jpg"
            namespace = uuid5(NAMESPACE_URL, "sauva-demo:" + name)
            if name == "example_imaging.jpeg":
                from app.extraction import normalize_jpeg
                normalize_jpeg(data)
                text, payload = IMAGE_NOTICE, imaging_bundle(data, fmt, namespace, name)
            else:
                missing = [key for key in ("GEMINI_API_KEY", "GEMINI_MODEL") if not os.getenv(key)]
                if missing:
                    raise ValueError("Configure GEMINI_API_KEY e GEMINI_MODEL localmente.")
                text, payload = gemini_convert_file(data, fmt)
            (output / (name + ".extracted.txt")).write_text(text, encoding="utf-8")
            candidate = output / (name + ".candidate.json")
            save(candidate, payload)
            entry["candidate"] = candidate.name
            payload = validate_bundle(normalize_bundle_ids(payload, namespace=namespace))
            target = output / (name + ".fhir.json")
            save(target, payload)
            entry.update({
                "status": "ready", "validation_level": "structural",
                "extracted_chars": len(text), "output": target.name,
                "resources": dict(Counter(item["resource"]["resourceType"] for item in payload["entry"])),
            })
            print(name + ": JSON gerado; revisar fidelidade ao original.")
        except Exception as error:
            entry.update({
                "status": "error", "error_type": type(error).__name__,
                "error_message": safe_error(error),
            })
            save(ledger_path, ledger)
            print(name + ": " + entry["error_type"] + ": " + entry["error_message"])
            print("Sem retry; os demais arquivos continuam. Corrija antes de --retry-failed " + name)
            failures += 1
        finally:
            save(ledger_path, ledger)
    save(ledger_path, ledger)
    print("Resultados: generated/demo-gemini/; zero chamadas Vision.")
    print("Validação estrutural apenas; imagem preservada sem interpretação diagnóstica.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
