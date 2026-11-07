"""Validação estrutural local; não certifica conformidade BR Core."""

import re


def validate_bundle(bundle: object) -> dict:
    if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
        raise ValueError("Bundle FHIR inválido.")
    if bundle.get("type") not in {"collection", "document"}:
        raise ValueError("Tipo de Bundle inválido.")
    entries = bundle.get("entry")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Bundle sem recursos.")
    urls, ids, refs = set(), set(), []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("resource"), dict):
            raise ValueError("Entrada FHIR inválida.")
        resource = entry["resource"]
        kind, ident, url = resource.get("resourceType"), resource.get("id"), entry.get("fullUrl")
        if not isinstance(kind, str) or not re.fullmatch(r"[A-Z][A-Za-z0-9]+", kind):
            raise ValueError("Tipo de recurso inválido.")
        if not isinstance(ident, str) or not re.fullmatch(r"[A-Za-z0-9.\-]{1,64}", ident):
            raise ValueError("ID de recurso inválido.")
        if not isinstance(url, str) or not url or url in urls or (kind, ident) in ids:
            raise ValueError("Identificador duplicado ou ausente.")
        urls.add(url)
        ids.add((kind, ident))
        if kind == "Observation" and not resource.get("status") or kind == "Observation" and not resource.get("code"):
            raise ValueError("Observation incompleta.")
        if kind == "Condition" and not resource.get("subject"):
            raise ValueError("Condition incompleta.")
        if kind == "MedicationRequest" and not all(resource.get(k) for k in ("status", "intent", "medicationCodeableConcept", "subject")):
            raise ValueError("MedicationRequest incompleta.")
        def collect(value):
            if isinstance(value, dict):
                if "reference" in value:
                    refs.append(value["reference"])
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)
        collect(resource)
    for ref in refs:
        if not isinstance(ref, str) or (ref not in urls and not any(ref == f"{kind}/{ident}" for kind, ident in ids)):
            raise ValueError("Referência interna não resolvida.")
    if bundle["type"] == "document":
        composition = entries[0]["resource"]
        if composition.get("resourceType") != "Composition" or not all(composition.get(k) for k in ("status", "type", "date", "title", "subject", "author")):
            raise ValueError("Composition obrigatória no início do documento.")
    return bundle
