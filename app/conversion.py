"""Adaptadores Google: execução explícita, tempo limitado e sem retries."""
import json
import os
from pathlib import Path

MAX_TEXT_CHARS = 60_000


def real_google_enabled() -> bool:
    return (
        os.getenv("ENABLE_REAL_GOOGLE", "false").lower() == "true"
        and os.getenv("FHIR_PROMPT_APPROVED", "false").lower() == "true"
    )


def vision_ocr(image_bytes: bytes) -> str:
    if not real_google_enabled():
        raise RuntimeError("Integração Google desativada.")
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()
    try:
        result = client.text_detection(
            image=vision.Image(content=image_bytes), timeout=30, retry=None,
        )
        if result.error.message or not result.text_annotations:
            raise RuntimeError("OCR não retornou texto.")
        text = result.text_annotations[0].description.strip()
        if not text:
            raise RuntimeError("OCR não retornou texto.")
        return text
    finally:
        client.transport.close()


def _json_response(response) -> dict:
    candidates = getattr(response, "candidates", None) or []
    reason = getattr(candidates[0], "finish_reason", None) if candidates else None
    reason = getattr(reason, "value", reason)
    if reason != "STOP":
        raise ValueError("Resposta Gemini interrompida ou bloqueada; conversão não concluída.")
    payload = json.loads(response.text)
    if not isinstance(payload, dict):
        raise ValueError("Resposta Gemini deve ser um objeto JSON.")
    return payload


def gemini_convert(text: str) -> dict:
    if not real_google_enabled() or not os.getenv("GEMINI_API_KEY") or not os.getenv("GEMINI_MODEL"):
        raise RuntimeError("Integração Gemini não configurada ou não aprovada.")
    if not text.strip() or len(text) > MAX_TEXT_CHARS:
        raise ValueError("Texto vazio ou acima do limite de conversão; nenhum trecho será truncado.")
    from google import genai
    from google.genai import types
    root = Path(__file__).resolve().parents[1] / "prompts"
    facts_prompt = (root / "01-extract.md").read_text(encoding="utf-8")
    map_prompt = (root / "02-map-fhir.md").read_text(encoding="utf-8")
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options=types.HttpOptions(
            timeout=60_000, retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    try:
        def generate(instructions, data):
            config = types.GenerateContentConfig(
                system_instruction=instructions, response_mime_type="application/json",
                max_output_tokens=8192, temperature=0.1,
            )
            response = client.models.generate_content(
                model=os.environ["GEMINI_MODEL"],
                contents=json.dumps(data, ensure_ascii=False), config=config,
            )
            return _json_response(response)

        facts = generate(facts_prompt, {"documento": text})
        if not isinstance(facts.get("facts"), list) or not facts["facts"]:
            raise ValueError("Nenhum fato clínico foi extraído; mapeamento não executado.")
        return generate(map_prompt, {"dados": facts})
    finally:
        client.close()
