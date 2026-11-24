"""Extraction, chunking, the local index and the grounded-answer logic."""

from __future__ import annotations

import io

import pytest

from app.chunking import Chunk, chunk_sections
from app.config import Settings
from app.embeddings import HashingEmbedder
from app.extraction import EmptyDocument, Section, UnsupportedFileType, extract_sections
from app.generation import ExtractiveGenerator, build_context, build_user_prompt
from app.rag import RagService
from app.storage import LocalStorage, safe_name
from app.vector_store import InMemoryStore, Match, chunk_id


class TestExtraction:
    def test_pdf_is_read_page_by_page(self, pdf_factory):
        sections = extract_sections("a.pdf", pdf_factory(["first page", "second page"]))
        assert [(s.location, s.text.strip()) for s in sections] == [
            ("page 1", "first page"),
            ("page 2", "second page"),
        ]

    def test_docx_and_pptx_are_read(self):
        from docx import Document
        from pptx import Presentation

        document = Document()
        document.add_paragraph("hello from word")
        docx_bytes = io.BytesIO()
        document.save(docx_bytes)

        deck = Presentation()
        slide = deck.slides.add_slide(deck.slide_layouts[5])
        slide.shapes.title.text = "hello from a slide"
        pptx_bytes = io.BytesIO()
        deck.save(pptx_bytes)

        assert "hello from word" in extract_sections("a.docx", docx_bytes.getvalue())[0].text
        slide_section = extract_sections("a.pptx", pptx_bytes.getvalue())[0]
        assert slide_section.location == "slide 1"
        assert "hello from a slide" in slide_section.text

    def test_unsupported_extension_is_rejected(self):
        with pytest.raises(UnsupportedFileType):
            extract_sections("malware.exe", b"MZ")

    def test_audio_needs_a_transcriber(self):
        with pytest.raises(UnsupportedFileType):
            extract_sections("talk.mp3", b"\x00")
        sections = extract_sections("talk.mp3", b"\x00", lambda name, data: "spoken words")
        assert sections == [Section(text="spoken words", location="transcript")]

    def test_a_file_without_text_is_reported(self, pdf_factory):
        with pytest.raises(EmptyDocument):
            extract_sections("blank.pdf", pdf_factory([""]))


class TestChunking:
    def test_chunks_keep_their_page_and_never_span_two(self):
        sections = [Section("alpha " * 60, "page 1"), Section("omega " * 60, "page 2")]
        chunks = chunk_sections("doc.pdf", sections, chunk_size=120, chunk_overlap=20)
        assert len(chunks) > 2
        assert all(len(chunk.text) <= 120 for chunk in chunks)
        assert [chunk.position for chunk in chunks] == list(range(len(chunks)))
        for chunk in chunks:
            word = "alpha" if chunk.location == "page 1" else "omega"
            assert (
                word in chunk.text and ("omega" if word == "alpha" else "alpha") not in chunk.text
            )


class TestLocalIndex:
    def _index(self, texts):
        embedder, store = HashingEmbedder(), InMemoryStore()
        chunks = [Chunk(text, "doc.pdf", f"page {i}", i) for i, text in enumerate(texts, 1)]
        store.upsert(chunks, embedder.embed(texts))
        return embedder, store

    def test_the_closest_chunk_ranks_first(self):
        embedder, store = self._index(
            ["cats sleep most of the day", "the invoice is due in thirty days"]
        )
        [vector] = embedder.embed(["when is the invoice due"])
        matches = store.query(vector, top_k=2)
        assert matches[0].location == "page 2"
        assert matches[0].score > matches[-1].score or len(matches) == 1

    def test_unrelated_questions_return_nothing(self):
        embedder, store = self._index(["cats sleep most of the day"])
        [vector] = embedder.embed(["quarterly revenue forecast"])
        assert store.query(vector, top_k=3) == []

    def test_reuploading_a_file_does_not_duplicate_chunks(self):
        embedder, store = self._index(["one", "two"])
        chunks = [Chunk("one edited", "doc.pdf", "page 1", 1)]
        store.upsert(chunks, embedder.embed(["one edited"]))
        assert store.count() == 2
        assert chunk_id(chunks[0]) == chunk_id(Chunk("anything", "doc.pdf", "page 9", 1))


class TestContextAndPrompt:
    def test_a_single_match_is_used_as_context(self):
        # Regression: the first version returned an empty context with exactly one match.
        context, used = build_context([Match("only passage", "a.pdf", "page 1", 0.9)], 1000)
        assert "only passage" in context and len(used) == 1

    def test_context_stops_at_the_limit_and_reports_what_it_used(self):
        matches = [Match("x" * 40, "a.pdf", f"page {i}", 1.0 - i / 10) for i in range(1, 5)]
        context, used = build_context(matches, max_chars=130)
        assert len(context) <= 130
        assert [m.location for m in used] == ["page 1", "page 2"]

    def test_the_prompt_carries_context_and_question(self):
        prompt = build_user_prompt("what is due?", "CTX")
        assert prompt.index("CTX") < prompt.index("what is due?")

    def test_extractive_answers_quote_the_best_passages(self):
        matches = [Match(f"passage {i}", "a.pdf", f"page {i}", 1.0) for i in range(1, 4)]
        answer = ExtractiveGenerator(passages=2).answer("q", "ctx", matches)
        assert "passage 1" in answer and "passage 2" in answer and "passage 3" not in answer


class TestService:
    def _service(self, tmp_path, generator=None):
        return RagService(
            HashingEmbedder(),
            InMemoryStore(),
            generator or ExtractiveGenerator(),
            LocalStorage(str(tmp_path)),
            chunk_size=200,
            chunk_overlap=20,
            top_k=3,
            max_context_chars=2000,
        )

    def test_ingest_then_answer_with_sources(self, tmp_path, pdf_factory):
        service = self._service(tmp_path)
        result = service.ingest(
            "report.pdf", pdf_factory(["Cats sleep all day.", "The invoice is due in thirty days."])
        )
        assert result.chunks == 2 and service.has_documents()
        answer = service.answer("When is the invoice due?")
        assert "thirty days" in answer.text
        assert answer.sources[0].source == "report.pdf"
        assert answer.sources[0].location == "page 2"

    def test_no_documents_means_no_generation(self, tmp_path):
        class Exploding:
            def answer(self, *args):
                raise AssertionError("the generator must not be called without context")

        answer = self._service(tmp_path, Exploding()).answer("anything at all?")
        assert answer.sources == [] and "could not find" in answer.text

    def test_empty_questions_are_rejected(self, tmp_path):
        with pytest.raises(ValueError):
            self._service(tmp_path).answer("   ")

    def test_document_text_cannot_escape_the_storage_folder(self, tmp_path):
        assert safe_name("../../etc/passwd") == "passwd"
        assert safe_name("..\\..\\boot.ini") == "boot.ini"
        assert safe_name("my report (final).pdf") == "my_report_final_.pdf"
        service = self._service(tmp_path / "docs")
        location = service.ingest("../outside.txt", b"some text here").location
        assert (tmp_path / "docs" / "outside.txt").samefile(location)


class TestSettings:
    def test_local_is_the_default_without_keys(self):
        assert Settings.from_env({}).backend == "local"

    def test_cloud_is_chosen_when_both_keys_are_present(self):
        settings = Settings.from_env({"OPENAI_API_KEY": "k", "PINECONE_API_KEY": "k"})
        assert settings.backend == "cloud"

    def test_cloud_without_keys_fails_early(self):
        with pytest.raises(ValueError):
            Settings.from_env({"RAG_BACKEND": "cloud"})

    def test_names_from_the_first_version_are_still_read(self):
        settings = Settings.from_env({"YOUR_INDEX_NAME": "old", "YOUR_BUCKET_NAME": "bucket"})
        assert (settings.pinecone_index, settings.s3_bucket) == ("old", "bucket")
