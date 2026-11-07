"""Smoke real de uma página SINTÉTICA. Não executar antes de aprovar prompts."""
from collections import Counter
from io import BytesIO
import os
from pathlib import Path
import time
from urllib.parse import urlparse

from dotenv import load_dotenv
import httpx
from reportlab.pdfgen.canvas import Canvas


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    required = ("GEMINI_API_KEY", "GEMINI_MODEL", "DEMO_OWNER_PASSWORD")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise SystemExit("Configuração ausente: " + ", ".join(missing))
    if any(os.getenv(name, "").lower() != "true" for name in
           ("ENABLE_REAL_GOOGLE", "FHIR_PROMPT_APPROVED")):
        raise SystemExit("Aprovar os prompts antes de ativar as duas flags Google.")
    origin = os.getenv("APP_ORIGIN", "http://127.0.0.1:8000")
    parsed = urlparse(origin)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Este smoke aceita somente o servidor local.")
    output = BytesIO()
    pdf = Canvas(output)
    for index, line in enumerate((
        "REGISTRO SINTETICO PARA TESTE - SEM DADOS REAIS",
        "Paciente: Pessoa Sintetica. Temperatura: 37 C.",
        "Sem identificadores, data ou autoria informados.",
    )):
        pdf.drawString(40, 750 - index * 22, line)
    pdf.save()
    # Uma submissão de PDF textual: zero Vision; no máximo duas Gemini.
    # Sem retries do HTTP ou do SDK, sem novos uploads em caso de falha.
    with httpx.Client(base_url=origin, timeout=15) as client:
        response = client.post("/auth/login", headers={"Origin": origin}, json={
            "email": "demo1@sauva.example", "password": os.environ["DEMO_OWNER_PASSWORD"],
        })
        if response.status_code != 200:
            raise SystemExit(f"Login local falhou (HTTP {response.status_code}); confira seed/senha.")
        try:
            response = client.post("/documents", headers={"Origin": origin},
                data={"document_type": "Texto", "name": "Smoke sintético"},
                files={"file": ("smoke_sintetico.pdf", output.getvalue(), "application/pdf")})
            if response.status_code != 202:
                raise SystemExit(f"Upload falhou (HTTP {response.status_code}); nenhum reenvio.")
            ident = response.json()["id"]
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                response = client.get(f"/documents/{ident}")
                if response.status_code != 200:
                    raise SystemExit(f"Consulta falhou (HTTP {response.status_code}).")
                info = response.json()
                if info["status"] == "error":
                    raise SystemExit("Conversão falhou. Não reenviar automaticamente; revisar configuração e erro local.")
                if info["status"] == "ready":
                    result = client.get(f"/documents/{ident}/json")
                    if result.status_code != 200:
                        raise SystemExit(f"Download falhou (HTTP {result.status_code}).")
                    bundle = result.json()
                    counts = Counter(entry["resource"]["resourceType"] for entry in bundle["entry"])
                    print("Smoke concluído:", ident)
                    print("Recursos:", dict(counts))
                    print("Revisar manualmente fatos/negações e ausência de dados inventados.")
                    print("Validação estrutural apenas; este resultado não comprova BR Core.")
                    return 0
                time.sleep(2)
            raise SystemExit("Tempo de espera esgotado. O job pode continuar; não reenviar.")
        finally:
            client.post("/auth/logout", headers={"Origin": origin})
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
