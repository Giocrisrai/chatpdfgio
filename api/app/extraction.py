"""Turn an uploaded file into plain text, one entry per page or slide."""

from __future__ import annotations

import io
from collections.abc import Callable
from dataclasses import dataclass

TEXT_EXTENSIONS = {"pdf", "docx", "pptx", "txt", "md"}
AUDIO_EXTENSIONS = {"mp3", "m4a", "wav"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | AUDIO_EXTENSIONS

Transcriber = Callable[[str, bytes], str]


class UnsupportedFileType(ValueError):
    """The file extension is not one the pipeline can read."""


class EmptyDocument(ValueError):
    """The file was read but contains no extractable text."""


@dataclass(frozen=True)
class Section:
    """A unit of source text and where it came from inside the document."""

    text: str
    location: str  # "page 3", "slide 2", "document" ...


def extension_of(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _pdf(data: bytes) -> list[Section]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return [
        Section(text=page.extract_text() or "", location=f"page {number}")
        for number, page in enumerate(reader.pages, start=1)
    ]


def _docx(data: bytes) -> list[Section]:
    from docx import Document

    document = Document(io.BytesIO(data))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    return [Section(text=text, location="document")]


def _pptx(data: bytes) -> list[Section]:
    from pptx import Presentation

    sections = []
    for number, slide in enumerate(Presentation(io.BytesIO(data)).slides, start=1):
        lines = [shape.text_frame.text for shape in slide.shapes if shape.has_text_frame]
        sections.append(Section(text="\n".join(lines), location=f"slide {number}"))
    return sections


def extract_sections(
    filename: str, data: bytes, transcriber: Transcriber | None = None
) -> list[Section]:
    """Return the non-empty text sections of a file.

    Audio files are transcribed with ``transcriber``; without one they are
    rejected, which is what the local backend does.
    """
    extension = extension_of(filename)
    if extension == "pdf":
        sections = _pdf(data)
    elif extension == "docx":
        sections = _docx(data)
    elif extension == "pptx":
        sections = _pptx(data)
    elif extension in {"txt", "md"}:
        sections = [Section(text=data.decode("utf-8", errors="replace"), location="document")]
    elif extension in AUDIO_EXTENSIONS:
        if transcriber is None:
            raise UnsupportedFileType("audio files need the cloud backend (a transcription model)")
        sections = [Section(text=transcriber(filename, data), location="transcript")]
    else:
        raise UnsupportedFileType(
            f"unsupported file type: .{extension or '?'} "
            f"(supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))})"
        )
    sections = [section for section in sections if section.text.strip()]
    if not sections:
        raise EmptyDocument(f"{filename} has no extractable text (a scanned PDF needs OCR first)")
    return sections
