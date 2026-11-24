"""Split document sections into overlapping chunks ready to be embedded."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.extraction import Section


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str  # file name
    location: str  # page / slide inside the file
    position: int  # order of the chunk inside the document


def chunk_sections(
    source: str, sections: list[Section], chunk_size: int, chunk_overlap: int
) -> list[Chunk]:
    """Chunk each section on its own, so a chunk never spans two pages."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks: list[Chunk] = []
    for section in sections:
        for piece in splitter.split_text(section.text):
            if piece.strip():
                chunks.append(
                    Chunk(
                        text=piece.strip(),
                        source=source,
                        location=section.location,
                        position=len(chunks),
                    )
                )
    return chunks
