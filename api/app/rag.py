"""The RAG pipeline: ingest documents, then answer questions grounded on them."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.chunking import chunk_sections
from app.embeddings import Embedder
from app.extraction import Transcriber, extract_sections
from app.generation import NO_CONTEXT_ANSWER, Generator, build_context
from app.storage import DocumentStorage, safe_name
from app.vector_store import VectorStore


@dataclass(frozen=True)
class IngestResult:
    filename: str
    chunks: int
    location: str


@dataclass(frozen=True)
class Source:
    source: str
    location: str
    score: float


@dataclass(frozen=True)
class Answer:
    text: str
    sources: list[Source] = field(default_factory=list)


class RagService:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        generator: Generator,
        storage: DocumentStorage,
        *,
        chunk_size: int,
        chunk_overlap: int,
        top_k: int,
        max_context_chars: int,
        transcriber: Transcriber | None = None,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._generator = generator
        self._storage = storage
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._top_k = top_k
        self._max_context_chars = max_context_chars
        self._transcriber = transcriber

    def ingest(self, filename: str, data: bytes) -> IngestResult:
        """Extract, chunk, embed and index one file. Raises ``ValueError`` on bad input."""
        name = safe_name(filename)
        sections = extract_sections(name, data, self._transcriber)
        chunks = chunk_sections(name, sections, self._chunk_size, self._chunk_overlap)
        location = self._storage.save(name, data)
        vectors = self._embedder.embed([chunk.text for chunk in chunks])
        self._store.upsert(chunks, vectors)
        return IngestResult(filename=name, chunks=len(chunks), location=location)

    def answer(self, question: str) -> Answer:
        question = question.strip()
        if not question:
            raise ValueError("the question is empty")
        [vector] = self._embedder.embed([question])
        matches = self._store.query(vector, self._top_k)
        context, used = build_context(matches, self._max_context_chars)
        if not used:
            return Answer(text=NO_CONTEXT_ANSWER)
        text = self._generator.answer(question, context, used)
        sources = _unique_sources(used)
        return Answer(text=text or NO_CONTEXT_ANSWER, sources=sources)

    def has_documents(self) -> bool:
        return self._store.count() > 0 or self._storage.has_documents()


def _unique_sources(matches) -> list[Source]:
    """One entry per (file, page), keeping the best score, in rank order."""
    seen: dict[tuple[str, str], Source] = {}
    for match in matches:
        key = (match.source, match.location)
        if key not in seen:
            seen[key] = Source(
                source=match.source, location=match.location, score=round(match.score, 4)
            )
    return list(seen.values())
