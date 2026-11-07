"""Extração local de PDF e normalização de JPEG para OCR."""

from io import BytesIO

from PIL import Image
from pypdf import PdfReader


def normalize_jpeg(data: bytes) -> bytes:
    with Image.open(BytesIO(data)) as image:
        if image.format != "JPEG":
            raise ValueError("JPEG inválido.")
        image.load()
        output = BytesIO()
        image.convert("RGB").save(output, format="JPEG")
        return output.getvalue()


def pdf_pages(data: bytes) -> int:
    reader = PdfReader(BytesIO(data), strict=False)
    if reader.is_encrypted:
        raise ValueError("PDF protegido por senha.")
    count = len(reader.pages)
    if count < 1 or count > 10:
        raise ValueError("PDF deve ter entre 1 e 10 páginas.")
    return count


def extract(data: bytes, fmt: str, ocr) -> str:
    if fmt == "jpg":
        return ocr(normalize_jpeg(data))
    reader = PdfReader(BytesIO(data), strict=False)
    parts = []
    rendered = None
    try:
        for index, page in enumerate(reader.pages):
            content = (page.extract_text() or "").strip()
            if not content:
                if rendered is None:
                    import pypdfium2 as pdfium
                    rendered = pdfium.PdfDocument(data)
                pdf_page = rendered[index]
                try:
                    bitmap = pdf_page.render(scale=150 / 72)
                    image = bitmap.to_pil()
                    try:
                        output = BytesIO()
                        image.convert("RGB").save(output, format="JPEG")
                        content = ocr(output.getvalue())
                    finally:
                        image.close()
                        bitmap.close()
                finally:
                    pdf_page.close()
            parts.append(f"Página {index + 1}\n{content}")
    finally:
        if rendered is not None:
            rendered.close()
    return "\n\n".join(parts)
