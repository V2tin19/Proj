"""Document text extraction for .docx, .pdf, .txt, .md files."""

from __future__ import annotations

from io import BytesIO
from typing import Tuple

from docx import Document as DocxDocument


def parse_docx(file_bytes: bytes) -> str:
    """Extract plain text from a .docx file."""
    doc = DocxDocument(BytesIO(file_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def parse_pdf(file_bytes: bytes) -> str:
    """Extract plain text from a .pdf file using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        # fallback to older import path
        from PyPDF2 import PdfReader

    reader = PdfReader(BytesIO(file_bytes))
    texts: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            texts.append(text.strip())
    return "\n".join(texts)


def parse_txt(file_bytes: bytes) -> str:
    """Decode text file with UTF-8 fallback."""
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("gbk", errors="ignore")


def parse_file(filename: str, file_bytes: bytes) -> Tuple[str, str]:
    """Parse uploaded file and return (filename, text).

    Raises ValueError for unsupported file types.
    """
    lower_name = filename.lower()
    if lower_name.endswith(".docx"):
        return filename, parse_docx(file_bytes)
    if lower_name.endswith(".pdf"):
        return filename, parse_pdf(file_bytes)
    if lower_name.endswith(".txt") or lower_name.endswith(".md"):
        return filename, parse_txt(file_bytes)
    raise ValueError(f"不支持的文件类型: {filename}，仅支持 .docx, .pdf, .txt, .md")
