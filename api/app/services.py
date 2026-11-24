"""Build the RAG service for the configured backend. External clients are created here only."""

from __future__ import annotations

import io

from app.config import Settings
from app.embeddings import HashingEmbedder, OpenAIEmbedder
from app.generation import ExtractiveGenerator, OpenAIGenerator
from app.rag import RagService
from app.storage import LocalStorage, S3Storage
from app.vector_store import InMemoryStore, PineconeStore


def _storage(settings: Settings):
    if settings.s3_bucket:
        import boto3

        # Credentials come from the standard AWS chain (env vars, profile, role).
        return S3Storage(boto3.client("s3", region_name=settings.aws_region), settings.s3_bucket)
    return LocalStorage(settings.documents_dir)


def build_service(settings: Settings) -> RagService:
    common = dict(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        top_k=settings.top_k,
        max_context_chars=settings.max_context_chars,
    )
    if settings.backend == "local":
        return RagService(
            HashingEmbedder(), InMemoryStore(), ExtractiveGenerator(), _storage(settings), **common
        )

    from openai import OpenAI
    from pinecone import Pinecone

    openai_client = OpenAI(api_key=settings.openai_api_key)
    pinecone_client = Pinecone(api_key=settings.pinecone_api_key)

    def transcribe(filename: str, data: bytes) -> str:
        audio = io.BytesIO(data)
        audio.name = filename
        return openai_client.audio.transcriptions.create(
            model=settings.transcription_model, file=audio, response_format="text"
        )

    return RagService(
        OpenAIEmbedder(openai_client, settings.embedding_model, settings.embedding_dimensions),
        PineconeStore(
            pinecone_client,
            settings.pinecone_index,
            settings.embedding_dimensions,
            settings.pinecone_cloud,
            settings.pinecone_region,
            settings.pinecone_namespace,
        ),
        OpenAIGenerator(openai_client, settings.chat_model),
        _storage(settings),
        transcriber=transcribe,
        **common,
    )
