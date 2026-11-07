"""Validação estrutural local; não certifica conformidade BR Core."""

import re
from copy import deepcopy
from uuid import UUID, uuid4, uuid5

# Subconjunto clínico suportado pelo protótipo; não é validação de perfis.
SUPPORTED_TYPES = {
    'Patient', 'Practitioner', 'PractitionerRole', 'Organization', 'Encounter',
    'Condition', 'AllergyIntolerance', 'Observation', 'Medication',
    'MedicationRequest', 'MedicationStatement', 'MedicationAdministration',
    'MedicationDispense', 'DiagnosticReport', 'ServiceRequest', 'Procedure',
    'CarePlan', 'CareTeam', 'Composition', 'Location', 'HealthcareService',
    'Immunization', 'Specimen', 'RelatedPerson', 'DocumentReference', 'Binary',
    'ImagingStudy', 'Media', 'Provenance', 'ClinicalImpression', 'Group',
}


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
        if not isinstance(kind, str) or kind not in SUPPORTED_TYPES:
            raise ValueError("Tipo de recurso inválido.")
        if not isinstance(ident, str) or not re.fullmatch(r"[A-Za-z0-9.\-]{1,64}", ident):
            raise ValueError("ID de recurso inválido.")
        if not isinstance(url, str) or not url or url in urls or (kind, ident) in ids:
            raise ValueError("Identificador duplicado ou ausente.")
        if url.startswith("urn:uuid:"):
            try:
                UUID(url[len("urn:uuid:"):])
            except ValueError:
                raise ValueError("fullUrl urn:uuid malformado.") from None
        urls.add(url)
        ids.add((kind, ident))
        if kind == "Observation" and not all(resource.get(k) for k in ("status", "code")):
            raise ValueError("Observation incompleta.")
        if kind == "ClinicalImpression":
            subject = resource.get("subject")
            if resource.get("status") not in {"in-progress", "completed", "entered-in-error"}:
                raise ValueError("ClinicalImpression.status ausente ou inválido.")
            if not isinstance(subject, dict) or not subject.get("reference"):
                raise ValueError("ClinicalImpression.subject ausente.")
        if kind == "Condition" and not resource.get("subject"):
            raise ValueError("Condition incompleta.")
        if kind == "MedicationRequest":
            medication_choices = sum(k in resource for k in ("medicationCodeableConcept", "medicationReference"))
            if medication_choices != 1 or not all(resource.get(k) for k in ("status", "intent", "subject")):
                raise ValueError("MedicationRequest incompleta ou com medication[x] ambíguo.")
            medication = resource.get("medicationCodeableConcept", resource.get("medicationReference"))
            if not isinstance(medication, dict) or not medication:
                raise ValueError("Medicamento ausente.")
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
    patient_targets = {
        alias
        for entry in entries
        if entry["resource"]["resourceType"] in {"Patient", "Group"}
        for alias in (entry["fullUrl"], f'{entry["resource"]["resourceType"]}/{entry["resource"]["id"]}')
    }
    for entry in entries:
        resource = entry["resource"]
        if resource["resourceType"] == "ClinicalImpression" and resource["subject"]["reference"] not in patient_targets:
            raise ValueError("ClinicalImpression.subject deve apontar para Patient ou Group.")
    if bundle["type"] == "document":
        composition = entries[0]["resource"]
        if composition.get("resourceType") != "Composition" or not all(composition.get(k) for k in ("status", "type", "date", "title", "subject", "author")):
            raise ValueError("Composition obrigatória no início do documento.")
    return bundle


def normalize_bundle_ids(bundle: object, namespace=None) -> dict:
    """IDs técnicos por documento, sem completar fatos clínicos ou referências ausentes."""
    if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
        raise ValueError("Bundle FHIR inválido.")
    result = deepcopy(bundle)
    scope = UUID(str(namespace)) if namespace is not None else uuid4()
    result["id"] = str(scope)
    entries = result.get("entry")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Bundle sem recursos.")
    aliases = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("resource"), dict):
            raise ValueError("Entrada FHIR inválida.")
        resource = entry["resource"]
        kind, old_id, old_url = resource.get("resourceType"), resource.get("id"), entry.get("fullUrl")
        if not isinstance(kind, str) or kind not in SUPPORTED_TYPES:
            raise ValueError("Tipo de recurso inválido.")
        if not isinstance(old_id, str) or not re.fullmatch(r"[A-Za-z0-9.\-]{1,64}", old_id):
            raise ValueError("ID de origem inválido.")
        if not isinstance(old_url, str) or not old_url:
            raise ValueError("fullUrl de origem ausente.")
        keys = {old_url, f"{kind}/{old_id}"}
        if any(key in aliases for key in keys):
            raise ValueError("Identidade de recurso ambígua ou duplicada.")
        new_id = str(uuid5(scope, f"{kind}/{old_id}"))
        new_url = "urn:uuid:" + new_id
        for key in keys:
            aliases[key] = new_url
        resource["id"] = new_id
        entry["fullUrl"] = new_url
        if kind == "Patient":
            systems = {
                "http://www.saude.gov.br/fhir/sid/cpf": "https://saude.gov.br/fhir/sid/cpf",
                "http://www.saude.gov.br/fhir/sid/cns": "https://saude.gov.br/fhir/sid/cns",
            }
            for identifier in resource.get("identifier", []):
                if isinstance(identifier, dict) and isinstance(identifier.get("system"), str):
                    identifier["system"] = systems.get(identifier["system"], identifier["system"])

    def rewrite(value):
        if isinstance(value, dict):
            if isinstance(value.get("reference"), str):
                value["reference"] = aliases.get(value["reference"], value["reference"])
            for child in value.values():
                rewrite(child)
        elif isinstance(value, list):
            for child in value:
                rewrite(child)
    for entry in entries:
        rewrite(entry["resource"])
    return result
