"""Runtime configuration, read once from environment variables.

Two backends are supported:

* ``local`` (default when no API keys are set): hashing embeddings, an in-memory
  vector index and extractive answers. It needs no account and no network, so the
  whole pipeline can be run and tested anywhere.
* ``cloud``: OpenAI for embeddings and generation, Pinecone as the vector index.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    backend: str = "local"
    # OpenAI
    openai_api_key: str | None = None
    chat_model: str = "gpt-5-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    transcription_model: str = "gpt-4o-mini-transcribe"
    # Pinecone (serverless)
    pinecone_api_key: str | None = None
    pinecone_index: str = "chatpdfgio"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    pinecone_namespace: str = ""
    # Document storage: an S3 bucket when set, a local folder otherwise.
    s3_bucket: str | None = None
    aws_region: str | None = None
    documents_dir: str = "data/documents"
    # Retrieval
    chunk_size: int = 1200
    chunk_overlap: int = 150
    top_k: int = 6
    max_context_chars: int = 9000
    # Limits and CORS
    max_upload_mb: int = 25
    max_query_chars: int = 2000
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:8501"])

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Settings:
        env = dict(os.environ if env is None else env)
        openai_key = env.get("OPENAI_API_KEY") or None
        pinecone_key = env.get("PINECONE_API_KEY") or None
        default_backend = "cloud" if (openai_key and pinecone_key) else "local"
        backend = env.get("RAG_BACKEND", default_backend).lower()
        if backend not in {"local", "cloud"}:
            raise ValueError(f"RAG_BACKEND must be 'local' or 'cloud', got {backend!r}")
        if backend == "cloud" and not (openai_key and pinecone_key):
            raise ValueError(
                "RAG_BACKEND=cloud needs OPENAI_API_KEY and PINECONE_API_KEY to be set"
            )
        defaults = cls()
        return cls(
            backend=backend,
            openai_api_key=openai_key,
            chat_model=env.get("CHAT_MODEL", defaults.chat_model),
            embedding_model=env.get("EMBEDDING_MODEL", defaults.embedding_model),
            embedding_dimensions=int(
                env.get("EMBEDDING_DIMENSIONS", defaults.embedding_dimensions)
            ),
            transcription_model=env.get("TRANSCRIPTION_MODEL", defaults.transcription_model),
            pinecone_api_key=pinecone_key,
            # YOUR_INDEX_NAME / YOUR_BUCKET_NAME are the names the first version used.
            pinecone_index=env.get("PINECONE_INDEX")
            or env.get("YOUR_INDEX_NAME")
            or defaults.pinecone_index,
            pinecone_cloud=env.get("PINECONE_CLOUD", defaults.pinecone_cloud),
            pinecone_region=env.get("PINECONE_REGION", defaults.pinecone_region),
            pinecone_namespace=env.get("PINECONE_NAMESPACE", defaults.pinecone_namespace),
            s3_bucket=env.get("S3_BUCKET") or env.get("YOUR_BUCKET_NAME") or None,
            aws_region=env.get("AWS_REGION") or None,
            documents_dir=env.get("DOCUMENTS_DIR", defaults.documents_dir),
            chunk_size=int(env.get("CHUNK_SIZE", defaults.chunk_size)),
            chunk_overlap=int(env.get("CHUNK_OVERLAP", defaults.chunk_overlap)),
            top_k=int(env.get("TOP_K", defaults.top_k)),
            max_context_chars=int(env.get("MAX_CONTEXT_CHARS", defaults.max_context_chars)),
            max_upload_mb=int(env.get("MAX_UPLOAD_MB", defaults.max_upload_mb)),
            max_query_chars=int(env.get("MAX_QUERY_CHARS", defaults.max_query_chars)),
            cors_origins=_split(env["CORS_ORIGINS"])
            if env.get("CORS_ORIGINS")
            else defaults.cors_origins,
        )
