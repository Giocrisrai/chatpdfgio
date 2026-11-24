"""Embedding backends behind one small interface."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol


class Embedder(Protocol):
    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OpenAIEmbedder:
    """Embeddings from the OpenAI API, sent in batches."""

    def __init__(self, client, model: str, dimensions: int, batch_size: int = 64) -> None:
        self._client = client
        self._model = model
        self.dimensions = dimensions
        self._batch_size = batch_size

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = [text.replace("\n", " ") for text in texts[start : start + self._batch_size]]
            response = self._client.embeddings.create(
                model=self._model, input=batch, dimensions=self.dimensions
            )
            vectors.extend(item.embedding for item in response.data)
        return vectors


_WORD = re.compile(r"[a-z0-9áéíóúüñ]+")


class HashingEmbedder:
    """Deterministic bag-of-words embeddings that need no model and no network.

    Each word is hashed into one of ``dimensions`` buckets and the vector is
    L2-normalised, so cosine similarity measures word overlap. It is lexical, not
    semantic: good enough to run and test the pipeline offline, not a substitute
    for a real embedding model.
    """

    def __init__(self, dimensions: int = 512) -> None:
        self.dimensions = dimensions

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for word in _WORD.findall(text.lower()):
            digest = hashlib.blake2b(word.encode("utf-8"), digest_size=8).digest()
            vector[int.from_bytes(digest, "big") % self.dimensions] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]
