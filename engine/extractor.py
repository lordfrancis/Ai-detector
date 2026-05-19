"""Document text extraction utilities."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, Protocol

import fitz
from docx import Document


class UploadedFileLike(Protocol):
    name: str

    def read(self) -> bytes:
        ...

    def seek(self, offset: int) -> int:
        ...


def extract_text_from_txt(file: BinaryIO) -> str:
    """Extract text from a UTF-8 or UTF-8-BOM TXT file."""
    data = _read_bytes(file)
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("TXT file must be UTF-8 encoded.") from error


def extract_text_from_docx(file: BinaryIO) -> str:
    """Extract paragraph text from a DOCX file."""
    try:
        document = Document(file)
    except Exception as error:
        raise ValueError("Unable to read DOCX file.") from error

    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
    return "\n\n".join(paragraphs)


def extract_text_from_pdf(file: BinaryIO) -> str:
    """Extract text from a PDF with selectable text."""
    data = _read_bytes(file)
    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as error:
        raise ValueError("Unable to read PDF file.") from error

    page_text = []
    with document:
        for page in document:
            text = page.get_text("text").strip()
            if text:
                page_text.append(text)

    if not page_text:
        raise ValueError(
            "No extractable text found in this PDF. Scanned PDFs require OCR, "
            "which is not supported in this version."
        )

    return "\n\n".join(page_text)


def extract_text(uploaded_file: UploadedFileLike) -> str:
    """Extract text from a supported uploaded file based on its extension."""
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix == ".txt":
        return extract_text_from_txt(uploaded_file)
    if suffix == ".docx":
        return extract_text_from_docx(uploaded_file)
    if suffix == ".pdf":
        return extract_text_from_pdf(uploaded_file)

    raise ValueError("Unsupported file type. Upload a TXT, DOCX, or PDF file.")


def _read_bytes(file: BinaryIO) -> bytes:
    try:
        file.seek(0)
    except (AttributeError, OSError):
        pass
    data = file.read()
    if isinstance(data, str):
        return data.encode("utf-8")
    return data
