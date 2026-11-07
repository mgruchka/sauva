"""Exportação local e anexação de imagem; nenhuma chamada de IA."""
import base64
from io import BytesIO
from pathlib import Path
from uuid import uuid5
from xml.sax.saxutils import escape

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from PIL import Image as PILImage


IMAGE_NOTICE = "Imagem médica original preservada. Sem interpretação diagnóstica automática."


def imaging_bundle(data, fmt, ident, title):
    resource_id = str(uuid5(ident, "original-image"))
    return {"resourceType": "Bundle", "id": str(ident), "type": "collection", "entry": [{
        "fullUrl": "urn:uuid:" + resource_id,
        "resource": {"resourceType": "DocumentReference", "id": resource_id, "status": "current",
                     "description": IMAGE_NOTICE, "content": [{"attachment": {
                         "contentType": "application/pdf" if fmt == "pdf" else "image/jpeg",
                         "title": title, "data": base64.b64encode(data).decode("ascii")}}]}}]}


LABELS = {"Patient": "Paciente", "Observation": "Observação", "Condition": "Condição registrada",
          "MedicationRequest": "Prescrição", "ClinicalImpression": "Evolução clínica",
          "AllergyIntolerance": "Alergia", "Immunization": "Vacinação", "DocumentReference": "Documento original",
          "name": "Nome", "text": "Texto", "code": "Descrição", "status": "Estado",
          "birthDate": "Nascimento", "gender": "Sexo", "dosageInstruction": "Posologia",
          "valueQuantity": "Resultado", "value": "Valor", "unit": "Unidade",
          "medicationCodeableConcept": "Medicamento", "summary": "Resumo", "description": "Descrição"}


def readable_fields(value, path=""):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"id", "resourceType", "meta", "data", "div", "reference", "fullUrl", "system"}:
                continue
            yield from readable_fields(child, (path + " / " if path else "") + LABELS.get(key, key))
    elif isinstance(value, list):
        for child in value:
            yield from readable_fields(child, path)
    elif value is not None:
        yield path, str(value)


def render_pdf(doc):
    output = BytesIO()
    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#14472C")
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 14
    styles["BodyText"].splitLongWords = True
    story = []

    def paragraph(text, style="BodyText"):
        # Escape user/provider input: ReportLab's markup is never trusted.
        safe = escape(str(text).encode("latin-1", "replace").decode("latin-1"))
        story.append(Paragraph(safe.replace("\n", "<br/>"), styles[style]))
        story.append(Spacer(1, 6))

    paragraph("SAÚVA", "Title")
    paragraph(doc.name, "Heading1")
    paragraph("Protótipo - reprodução dos dados armazenados. Confira com o documento original.")
    paragraph("Validação estrutural parcial; conformidade BR Core e revisão clínica não certificadas.")
    if doc.document_type == "Exame de imagem":
        paragraph(IMAGE_NOTICE)
        if doc.file_format == "jpg":
            with PILImage.open(doc.storage_path) as source:
                source.load()
                preview = source.convert("RGB")
                preview.thumbnail((1600, 1600))
                image = BytesIO()
                preview.save(image, "JPEG")
                width, height = preview.size
            image.seek(0)
            scale = min(480 / width, 520 / height)
            story.append(Image(image, width * scale, height * scale))
    else:
        for entry in (doc.fhir_payload or {}).get("entry", []):
            resource = entry.get("resource", {})
            paragraph(LABELS.get(resource.get("resourceType"), resource.get("resourceType", "Registro")), "Heading2")
            for key, value in readable_fields(resource):
                # Chunk very long strings so a single paragraph cannot exceed a page.
                for start in range(0, len(value), 1800):
                    paragraph(f"{key}: {value[start:start + 1800]}")
        if doc.extracted_text:
            story.append(PageBreak())
            paragraph("Transcrição extraída - confira o original", "Heading1")
            for line in doc.extracted_text.splitlines():
                for start in range(0, len(line), 1800):
                    paragraph(line[start:start + 1800])

    def footer(canvas, document):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6E6259"))
        canvas.drawString(40, 24, "SAUVA - demonstracao")
        canvas.drawRightString(A4[0] - 40, 24, str(document.page))

    SimpleDocTemplate(output, pagesize=A4, rightMargin=40, leftMargin=40,
                      topMargin=35, bottomMargin=40, title=doc.name).build(story, onFirstPage=footer, onLaterPages=footer)
    if doc.document_type == "Exame de imagem" and doc.file_format == "pdf":
        writer = PdfWriter()
        writer.append(PdfReader(BytesIO(output.getvalue())))
        writer.append(PdfReader(Path(doc.storage_path)))
        combined = BytesIO()
        writer.write(combined)
        return combined.getvalue()
    return output.getvalue()
