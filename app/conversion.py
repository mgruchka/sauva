"""Adaptadores Google carregados somente na execução real."""

import json
import os
from pathlib import Path


def real_google_enabled() -> bool:
    return os.getenv("ENABLE_REAL_GOOGLE", "false").lower() == "true" and os.getenv("FHIR_PROMPT_APPROVED", "false").lower() == "true"


def vision_ocr(image_bytes: bytes) -> str:
    if not real_google_enabled():
        raise RuntimeError("Integração Google desativada.")
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()
    result = client.text_detection(image=vision.Image(content=image_bytes), timeout=30)
    if result.error.message or not result.text_annotations:
        raise RuntimeError("OCR não retornou texto.")
    return result.text_annotations[0].description


def gemini_convert(text: str) -> dict:
    if not real_google_enabled() or not os.getenv("GEMINI_API_KEY") or not os.getenv("GEMINI_MODEL"):
        raise RuntimeError("Integração Gemini não configurada ou não aprovada.")
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    root = Path(__file__).resolve().parents[1] / "prompts"
    facts_prompt = (root / "01-extract.md").read_text(encoding="utf-8")
    map_prompt = (root / "02-map-fhir.md").read_text(encoding="utf-8")
    config = types.GenerateContentConfig(response_mime_type="application/json", max_output_tokens=8192, temperature=0.1)
    facts = client.models.generate_content(model=os.environ["GEMINI_MODEL"], contents=f"{facts_prompt}\n<documento>\n{text}\n</documento>", config=config)
    parsed = json.loads(facts.text)
    result = client.models.generate_content(model=os.environ["GEMINI_MODEL"], contents=f"{map_prompt}\n<dados>\n{json.dumps(parsed, ensure_ascii=False)}\n</dados>", config=config)
    return json.loads(result.text)
