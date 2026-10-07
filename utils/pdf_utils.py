"""PDF text extraction using pypdf."""

import io

from pypdf import PdfReader


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract readable text from a PDF using PyPDF.

    Returns an empty string if the PDF contains no extractable text
    (e.g. a scanned or image-only document).
    """
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(text.strip() for text in pages if text.strip())
