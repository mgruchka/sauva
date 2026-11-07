"""Revalida candidatos existentes sem Google, banco ou credenciais."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.fhir import normalize_bundle_ids, validate_bundle


def save(path, payload):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def main():
    output = ROOT / "generated" / "demo-gemini"
    output.mkdir(parents=True, exist_ok=True)
    ledger_path = output / "report.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {
        "pipeline": "gemini-only-v1", "files": {}, "history": [],
    }
    ledger.setdefault("history", [])
    failed = False
    for name in ("example_text.pdf", "example_text-1.jpeg", "example_text-2.jpeg"):
        choices = [output / (name + ".candidate.json"),
                   ROOT / "demo-results/gemini-only" / (name + ".candidate.json"),
                   ROOT / "demo-results/gemini-only" / (name + ".fhir.json")]
        source = next((path for path in choices if path.is_file()), None)
        if source is None:
            print(name + ": candidato ausente; nenhuma inferência executada.")
            failed = True
            continue
        try:
            raw = source.read_bytes()
            payload = normalize_bundle_ids(
                json.loads(raw), namespace=uuid5(NAMESPACE_URL, "sauva-demo:" + name),
            )
            validate_bundle(payload)
            target = output / (name + ".fhir.json")
            save(target, payload)
            previous = deepcopy(ledger["files"].get(name, {}))
            digest = hashlib.sha256(raw).hexdigest()
            if previous and previous.get("normalized_source_sha256") != digest:
                ledger["history"].append({"file": name, "event": "offline_revalidation", **previous})
            updated = {key: value for key, value in previous.items()
                       if key not in {"error_type", "error_message", "provider_code"}}
            updated.update({
                "status": "ready", "validation_level": "structural",
                "output": target.name, "revalidated_offline": True,
                "normalized_source_sha256": digest,
                "last_offline_validation_at": datetime.now(timezone.utc).isoformat(),
            })
            ledger["files"][name] = updated
            print(name + ": validado localmente; zero chamadas Google.")
        except (ValueError, TypeError, KeyError) as error:
            print(name + ": falha local: " + str(error))
            failed = True
    save(ledger_path, ledger)
    print("Originais e banco preservados. Fidelidade clínica ainda requer revisão.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
