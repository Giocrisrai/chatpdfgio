"""Vector index backends: Pinecone for the cloud, an in-memory index for local runs."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.chunking import Chunk


@dataclass(frozen=True)
class Match:
    text: str
    source: str
    location: str
    score: float


class VectorStore(Protocol):
    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> int: ...

    def query(self, vector: Sequence[float], top_k: int) -> list[Match]: ...

    def count(self) -> int: ...


def chunk_id(chunk: Chunk) -> str:
    """Stable id: re-uploading the same file overwrites its chunks instead of duplicating them."""
    key = f"{chunk.source}\x00{chunk.position}".encode()
    return hashlib.sha1(key).hexdigest()


class InMemoryStore:
    """Exact cosine search over normalised vectors kept in a dict."""

    def __init__(self) -> None:
        self._items: dict[str, tuple[list[float], Chunk]] = {}

    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> int:
        for chunk, vector in zip(chunks, vectors, strict=True):
            self._items[chunk_id(chunk)] = (list(vector), chunk)
        return len(chunks)

    def query(self, vector: Sequence[float], top_k: int) -> list[Match]:
        scored = [
            (sum(a * b for a, b in zip(stored, vector, strict=True)), chunk)
            for stored, chunk in self._items.values()
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            Match(text=chunk.text, source=chunk.source, location=chunk.location, score=score)
            for score, chunk in scored[:top_k]
            if score > 0.0
        ]

    def count(self) -> int:
        return len(self._items)


class PineconeStore:
    """A Pinecone serverless index. The index is created on first use if missing."""

    def __init__(
        self,
        client,
        index_name: str,
        dimensions: int,
        cloud: str,
        region: str,
        namespace: str = "",
        batch_size: int = 100,
    ) -> None:
        self._client = client
        self._index_name = index_name
        self._dimensions = dimensions
        self._cloud = cloud
        self._region = region
        self._namespace = namespace
        self._batch_size = batch_size
        self._index = None

    def _get_index(self):
        if self._index is None:
            if not self._client.has_index(self._index_name):
                from pinecone import ServerlessSpec

                self._client.create_index(
                    name=self._index_name,
                    dimension=self._dimensions,
                    metric="cosine",
                    spec=ServerlessSpec(cloud=self._cloud, region=self._region),
                )
            self._index = self._client.Index(self._index_name)
        return self._index

    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> int:
        index = self._get_index()
        records = [
            (
                chunk_id(chunk),
                list(vector),
                {"text": chunk.text, "source": chunk.source, "location": chunk.location},
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        for start in range(0, len(records), self._batch_size):
            index.upsert(
                vectors=records[start : start + self._batch_size],
                namespace=self._namespace,
            )
        return len(records)

    def query(self, vector: Sequence[float], top_k: int) -> list[Match]:
        response = self._get_index().query(
            vector=list(vector),
            top_k=top_k,
            include_metadata=True,
            namespace=self._namespace,
        )
        matches = []
        for item in response.matches:
            metadata = item.metadata or {}
            if not metadata.get("text"):
                continue
            matches.append(
                Match(
                    text=metadata["text"],
                    source=metadata.get("source", "unknown"),
                    location=metadata.get("location", ""),
                    score=float(item.score),
                )
            )
        return matches

    def count(self) -> int:
        stats = self._get_index().describe_index_stats()
        return int(getattr(stats, "total_vector_count", 0) or 0)
