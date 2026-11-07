"""Regressões da revisão 03, sem banco, rede ou SDKs Google reais."""
from copy import deepcopy
import json
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch
import sys

from app.conversion import gemini_convert, vision_ocr
from app.fhir import validate_bundle


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
        client_args=[], calls=[], closed=0, vision_args=[], vision_closed=0,
        reason="STOP", facts=[{"text": "Fato sintético"}], ocr_text="Texto sintético",
    )
    google = ModuleType("google")
    google.__path__ = []
    genai = ModuleType("google.genai")
    types = ModuleType("google.genai.types")
    for name in ("GenerateContentConfig", "HttpOptions", "HttpRetryOptions"):
        setattr(types, name, lambda **kwargs: SimpleNamespace(**kwargs))

    def generate_content(**kwargs):
        state.calls.append(kwargs)
        payload = {"facts": state.facts} if len(state.calls) == 1 else prescription()
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
    cloud = ModuleType("google.cloud")
    cloud.__path__ = []
    vision = ModuleType("google.cloud.vision")

    def detect(**kwargs):
        state.vision_args.append(kwargs)
        return SimpleNamespace(
            error=SimpleNamespace(message=""),
            text_annotations=[SimpleNamespace(description=state.ocr_text)],
        )
    vision.Image = lambda **kwargs: SimpleNamespace(**kwargs)
    vision.ImageAnnotatorClient = lambda: SimpleNamespace(
        text_detection=detect,
        transport=SimpleNamespace(close=lambda: setattr(
            state, "vision_closed", state.vision_closed + 1,
        )),
    )
    cloud.vision, google.cloud = vision, cloud
    modules = {"google": google, "google.genai": genai, "google.genai.types": types,
               "google.cloud": cloud, "google.cloud.vision": vision}
    return state, modules


class Review03Tests(unittest.TestCase):
    def test_prescription_accepts_reference_and_rejects_dual_choice(self):
        value = prescription()
        self.assertIs(validate_bundle(value), value)
        invalid = deepcopy(value)
        invalid["entry"][2]["resource"]["medicationCodeableConcept"] = {"text": "Outro"}
        with self.assertRaises(ValueError):
            validate_bundle(invalid)

    def test_invented_resource_is_rejected(self):
        value = prescription()
        value["entry"][1]["resource"]["resourceType"] = "ImaginaryResource"
        with self.assertRaises(ValueError):
            validate_bundle(value)

    def test_gemini_two_calls_timeout_no_retry_and_client_closed(self):
        state, modules = google_fakes()
        with patch.dict(sys.modules, modules), patch.dict("os.environ", {
            "ENABLE_REAL_GOOGLE": "true", "FHIR_PROMPT_APPROVED": "true",
            "GEMINI_API_KEY": "synthetic-test-key", "GEMINI_MODEL": "synthetic-model",
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

    def test_vision_disables_retry_closes_transport_and_rejects_empty_text(self):
        for text in ("Texto sintético", " "):
            state, modules = google_fakes()
            state.ocr_text = text
            with patch.dict(sys.modules, modules), patch.dict("os.environ", {
                "ENABLE_REAL_GOOGLE": "true", "FHIR_PROMPT_APPROVED": "true",
            }):
                if text.strip():
                    self.assertEqual(vision_ocr(b"synthetic-image"), text)
                else:
                    with self.assertRaises(RuntimeError):
                        vision_ocr(b"synthetic-image")
            self.assertEqual(len(state.vision_args), 1)
            self.assertIsNone(state.vision_args[0]["retry"])
            self.assertEqual(state.vision_args[0]["timeout"], 30)
            self.assertEqual(state.vision_closed, 1)


if __name__ == "__main__":
    unittest.main()
