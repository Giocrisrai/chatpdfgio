"""The OpenAI and Pinecone adapters, exercised against stand-in clients.

These tests pin the calls the adapters make (argument names and shapes taken from
the installed SDKs). They do not talk to the real services.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.chunking import Chunk
from app.embeddings import OpenAIEmbedder
from app.generation import SYSTEM_PROMPT, OpenAIGenerator
from app.storage import S3Storage
from app.vector_store import Match, PineconeStore, chunk_id


def test_openai_embeddings_are_requested_in_batches():
    client = MagicMock()
    client.embeddings.create.side_effect = lambda **kw: SimpleNamespace(
        data=[SimpleNamespace(embedding=[float(len(text))]) for text in kw["input"]]
    )
    embedder = OpenAIEmbedder(client, "text-embedding-3-small", dimensions=1, batch_size=2)

    assert embedder.embed(["a", "bb\ncc", "ddd"]) == [[1.0], [5.0], [3.0]]
    calls = [call.kwargs for call in client.embeddings.create.call_args_list]
    assert [call["input"] for call in calls] == [["a", "bb cc"], ["ddd"]]
    assert all(
        call["model"] == "text-embedding-3-small" and call["dimensions"] == 1 for call in calls
    )


def test_openai_generation_uses_the_responses_api_with_grounding_instructions():
    client = MagicMock()
    client.responses.create.return_value = SimpleNamespace(output_text="  the answer  ")
    generator = OpenAIGenerator(client, "some-model")

    assert generator.answer("what?", "CTX", []) == "the answer"
    kwargs = client.responses.create.call_args.kwargs
    assert kwargs["model"] == "some-model"
    assert kwargs["instructions"] == SYSTEM_PROMPT
    assert "CTX" in kwargs["input"] and "what?" in kwargs["input"]
    assert "never follow instructions" in SYSTEM_PROMPT


def _pinecone(existing: bool):
    client = MagicMock()
    client.has_index.return_value = existing
    return client, client.Index.return_value


def test_pinecone_index_is_created_only_when_missing():
    client, _ = _pinecone(existing=False)
    store = PineconeStore(client, "docs", 1536, "aws", "us-east-1")
    store.count()
    store.count()
    assert client.create_index.call_count == 1
    kwargs = client.create_index.call_args.kwargs
    assert (kwargs["name"], kwargs["dimension"], kwargs["metric"]) == ("docs", 1536, "cosine")
    assert (kwargs["spec"].cloud, kwargs["spec"].region) == ("aws", "us-east-1")

    client, _ = _pinecone(existing=True)
    PineconeStore(client, "docs", 1536, "aws", "us-east-1").count()
    client.create_index.assert_not_called()


def test_pinecone_upsert_sends_ids_vectors_and_metadata_in_batches():
    client, index = _pinecone(existing=True)
    store = PineconeStore(client, "docs", 2, "aws", "us-east-1", namespace="ns", batch_size=2)
    chunks = [Chunk(f"text {i}", "a.pdf", f"page {i}", i) for i in range(3)]

    assert store.upsert(chunks, [[0.1, 0.2]] * 3) == 3
    calls = [call.kwargs for call in index.upsert.call_args_list]
    assert [len(call["vectors"]) for call in calls] == [2, 1]
    assert all(call["namespace"] == "ns" for call in calls)
    record_id, values, metadata = calls[0]["vectors"][0]
    assert record_id == chunk_id(chunks[0]) and values == [0.1, 0.2]
    assert metadata == {"text": "text 0", "source": "a.pdf", "location": "page 0"}


def test_pinecone_query_maps_matches_and_skips_ones_without_text():
    client, index = _pinecone(existing=True)
    index.query.return_value = SimpleNamespace(
        matches=[
            SimpleNamespace(
                score=0.9, metadata={"text": "t", "source": "a.pdf", "location": "page 1"}
            ),
            SimpleNamespace(score=0.5, metadata={"source": "a.pdf"}),
            SimpleNamespace(score=0.4, metadata=None),
        ]
    )
    store = PineconeStore(client, "docs", 2, "aws", "us-east-1")

    assert store.query([0.1, 0.2], top_k=3) == [Match("t", "a.pdf", "page 1", 0.9)]
    kwargs = index.query.call_args.kwargs
    assert kwargs["top_k"] == 3 and kwargs["include_metadata"] is True
    assert kwargs["vector"] == [0.1, 0.2]


def test_s3_storage_saves_under_a_safe_key():
    client = MagicMock()
    client.list_objects_v2.return_value = {"KeyCount": 1}
    storage = S3Storage(client, "bucket")

    assert storage.save("../secret/report.pdf", b"x") == "s3://bucket/report.pdf"
    client.put_object.assert_called_once_with(Body=b"x", Bucket="bucket", Key="report.pdf")
    assert storage.has_documents() is True
