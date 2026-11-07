"""Regressões da revisão 03, sem banco, rede ou SDKs Google reais."""
from copy import deepcopy
import json
from io import BytesIO

from PIL import Image
from reportlab.pdfgen.canvas import Canvas
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch
import sys

from app.conversion import gemini_convert, gemini_convert_file
from app.fhir import validate_bundle, normalize_bundle_ids


def prescription():
    return {"resourceType": "Bundle", "type": "collection", "entry": [
        {"fullUrl": "Patient/p", "resource": {"resourceType": "Patient", "id": "p"}},
        {"fullUrl": "Medication/m", "resource": {"resourceType": "Medication", "id": "m"}},
        {"fullUrl": "MedicationRequest/r", "resource": {
            "resourceType": "MedicationRequest", "id": "r", "status": "active",
            "intent": "order", "subject": {"reference": "Patient/p"},
            "medicationReference": {"reference": "Medication/m"},
        }},
    ]}


def google_fakes():
    state = SimpleNamespace(
        client_args=[], calls=[], closed=0,
        reason="STOP", facts=[{"text": "Fato sintético"}], transcription="Texto sintético",
    )
    google = ModuleType("google")
    google.__path__ = []
    genai = ModuleType("google.genai")
    types = ModuleType("google.genai.types")
    for name in ("GenerateContentConfig", "HttpOptions", "HttpRetryOptions"):
        setattr(types, name, lambda **kwargs: SimpleNamespace(**kwargs))

    def generate_content(**kwargs):
        state.calls.append(kwargs)
        payload = {"facts": state.facts, "transcription": state.transcription} if len(state.calls) == 1 else prescription()
        return SimpleNamespace(
            text=json.dumps(payload),
            candidates=[SimpleNamespace(finish_reason=state.reason)],
        )

    def client(**kwargs):
        state.client_args.append(kwargs)
        return SimpleNamespace(
            models=SimpleNamespace(generate_content=generate_content),
            close=lambda: setattr(state, "closed", state.closed + 1),
        )
    genai.Client, genai.types, google.genai = client, types, genai
    types.Part = SimpleNamespace(from_bytes=lambda **kwargs: SimpleNamespace(
        inline_data=SimpleNamespace(**kwargs),
    ))
    modules = {"google": google, "google.genai": genai, "google.genai.types": types}
    return state, modules


class Review03Tests(unittest.TestCase):
    def test_prescription_accepts_reference_and_rejects_dual_choice(self):
        value = prescription()
        self.assertIs(validate_bundle(value), value)
        invalid = deepcopy(value)
        invalid["entry"][2]["resource"]["medicationCodeableConcept"] = {"text": "Outro"}
        with self.assertRaises(ValueError):
            validate_bundle(invalid)
        value["entry"][0]["resource"]["identifier"] = [{
            "system": "http://www.saude.gov.br/fhir/sid/cpf", "value": "fixture-123",
        }]
        original = deepcopy(value)
        namespace = "00000000-0000-4000-8000-000000000001"
        normalized = normalize_bundle_ids(value, namespace=namespace)
        self.assertEqual(value, original)
        self.assertEqual(normalize_bundle_ids(value, namespace=namespace), normalized)
        validate_bundle(normalized)
        self.assertEqual(
            normalized["entry"][2]["resource"]["medicationReference"]["reference"],
            normalized["entry"][1]["fullUrl"],
        )
        identifier = normalized["entry"][0]["resource"]["identifier"][0]
        self.assertEqual(identifier["value"], "fixture-123")
        self.assertEqual(identifier["system"], "https://saude.gov.br/fhir/sid/cpf")
        invalid = deepcopy(normalized)
        invalid["entry"][1]["fullUrl"] = "urn:uuid:not-a-uuid"
        with self.assertRaises(ValueError):
            validate_bundle(invalid)
        invalid = deepcopy(value)
        invalid["entry"][2]["resource"]["subject"]["reference"] = "Patient/missing"
        with self.assertRaises(ValueError):
            validate_bundle(normalize_bundle_ids(invalid, namespace=namespace))

    def test_resource_types_and_clinical_impression_required_fields(self):
        value = prescription()
        value["entry"][1]["resource"]["resourceType"] = "ImaginaryResource"
        with self.assertRaises(ValueError):
            validate_bundle(value)
        value = prescription()
        value["entry"].append({
            "fullUrl": "ClinicalImpression/i",
            "resource": {"resourceType": "ClinicalImpression", "id": "i",
                         "status": "completed", "subject": {"reference": "Patient/p"},
                         "summary": "Avaliação documentada no exemplo sintético"},
        })
        validate_bundle(value)
        for change in ("missing_status", "bad_status", "missing_subject", "wrong_subject"):
            with self.subTest(change=change):
                invalid = deepcopy(value)
                target = invalid["entry"][-1]["resource"]
                if change == "missing_status":
                    target.pop("status")
                elif change == "bad_status":
                    target["status"] = "unknown"
                elif change == "missing_subject":
                    target.pop("subject")
                else:
                    target["subject"] = {"reference": "Medication/m"}
                with self.assertRaises(ValueError):
                    validate_bundle(invalid)

    def test_gemini_two_calls_timeout_no_retry_and_client_closed(self):
        state, modules = google_fakes()
        with patch.dict(sys.modules, modules), patch.dict("os.environ", {
            "ENABLE_REAL_GOOGLE": "true", "FHIR_PROMPT_APPROVED": "true",
            "GEMINI_API_KEY": "synthetic-test-key", "GEMINI_MODEL": "synthetic-model",
            "GEMINI_MIN_INTERVAL_SECONDS": "0",
        }):
            self.assertEqual(gemini_convert("Fato sintético")["resourceType"], "Bundle")
        self.assertEqual(len(state.calls), 2)
        options = state.client_args[0]["http_options"]
        self.assertEqual(options.timeout, 60000)
        self.assertEqual(options.retry_options.attempts, 1)
        self.assertEqual(state.closed, 1)
        self.assertTrue(state.calls[0]["config"].system_instruction)
        self.assertEqual(json.loads(state.calls[0]["contents"])["documento"], "Fato sintético")

    def test_incomplete_empty_and_oversized_inputs_stop_without_extra_calls(self):
        for text, reason, facts, expected in (
            (" ", "STOP", [{"text": "x"}], 0),
            ("x" * 60001, "STOP", [{"text": "x"}], 0),
            ("x", "MAX_TOKENS", [{"text": "x"}], 1),
            ("x", "STOP", [], 1),
        ):
            with self.subTest(size=len(text), reason=reason):
                state, modules = google_fakes()
                state.reason, state.facts = reason, facts
                with patch.dict(sys.modules, modules), patch.dict("os.environ", {
                    "ENABLE_REAL_GOOGLE": "true", "FHIR_PROMPT_APPROVED": "true",
                    "GEMINI_API_KEY": "synthetic-test-key", "GEMINI_MODEL": "synthetic-model",
                }):
                    with self.assertRaises(ValueError):
                        gemini_convert(text)
                self.assertEqual(len(state.calls), expected)
                self.assertEqual(state.closed, 1 if expected else 0)

    def test_scanned_pdf_and_jpeg_use_two_gemini_calls_without_vision(self):
        picture = BytesIO()
        Image.new("RGB", (80, 60), "white").save(picture, format="JPEG")

        def pdf_bytes(text):
            output = BytesIO()
            pdf = Canvas(output)
            for _ in range(2):
                if text:
                    pdf.drawString(40, 750, text)
                pdf.showPage()
            pdf.save()
            return output.getvalue()

        cases = [
            (picture.getvalue(), "jpg", "image/jpeg"),
            (pdf_bytes(""), "pdf", "application/pdf"),
            (pdf_bytes("Texto selecionavel"), "pdf", None),
        ]
        for data, fmt, expected_mime in cases:
            with self.subTest(fmt=fmt, multimodal=bool(expected_mime)):
                state, modules = google_fakes()
                with patch.dict(sys.modules, modules), patch.dict("os.environ", {
                    "ENABLE_REAL_GOOGLE": "true", "FHIR_PROMPT_APPROVED": "true",
                    "GEMINI_API_KEY": "synthetic-test-key", "GEMINI_MODEL": "synthetic-model",
                    "GEMINI_MIN_INTERVAL_SECONDS": "0",
                }):
                    transcription, value = gemini_convert_file(data, fmt)
                self.assertTrue(transcription)
                self.assertEqual(value["resourceType"], "Bundle")
                self.assertEqual(len(state.calls), 2)
                self.assertEqual(state.closed, 1)
                self.assertFalse(state.client_args[0]["vertexai"])
                contents = state.calls[0]["contents"]
                if expected_mime:
                    self.assertEqual(contents[1].inline_data.mime_type, expected_mime)
                else:
                    self.assertIn("Texto selecionavel", json.loads(contents)["documento"])


if __name__ == "__main__":
    unittest.main()
