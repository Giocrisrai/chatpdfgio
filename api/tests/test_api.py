"""The HTTP API end to end on the local backend."""

from __future__ import annotations


def test_health_reports_the_backend(client):
    assert client.get("/health").json() == {"status": "ok", "backend": "local"}


def test_upload_then_chat_returns_a_grounded_answer_with_sources(client, pdf_factory):
    assert client.get("/check-documents/").json()["message"] == "No documents loaded."

    pdf = pdf_factory(["Cats sleep all day.", "The invoice is due in thirty days."])
    upload = client.post(
        "/multipleupload/",
        files=[
            ("files", ("report.pdf", pdf, "application/pdf")),
            ("files", ("notes.txt", b"The office closes on Fridays at noon.", "text/plain")),
        ],
    )
    assert upload.status_code == 200
    assert [(r["filename"], r["status"]) for r in upload.json()["results"]] == [
        ("report.pdf", "Success"),
        ("notes.txt", "Success"),
    ]
    assert client.get("/check-documents/").json()["message"] == "Documents loaded."

    chat = client.post("/chat/", params={"query": "When is the invoice due?"})
    assert chat.status_code == 200
    body = chat.json()
    assert "thirty days" in body["response"]
    assert body["sources"][0]["source"] == "report.pdf"
    assert body["sources"][0]["location"] == "page 2"


def test_single_upload_endpoint(client):
    response = client.post("/upload/", files={"file": ("a.txt", b"hello world", "text/plain")})
    assert response.json()["status"] == "Success" and response.json()["chunks"] == 1


def test_bad_files_are_reported_per_file_without_failing_the_request(client, pdf_factory):
    response = client.post(
        "/multipleupload/",
        files=[
            ("files", ("tool.exe", b"MZ", "application/octet-stream")),
            ("files", ("blank.pdf", pdf_factory([""]), "application/pdf")),
            ("files", ("broken.pdf", b"not a pdf at all", "application/pdf")),
        ],
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert [r["status"] for r in results] == ["Failed", "Failed", "Failed"]
    assert "unsupported file type" in results[0]["message"]
    assert "no extractable text" in results[1]["message"]
    # Internal errors are not echoed back to the client.
    assert results[2]["message"] == "the file could not be processed"


def test_questions_are_validated(client):
    assert client.post("/chat/").status_code == 422
    assert client.post("/chat/", params={"query": "   "}).status_code == 422
    assert client.post("/chat/", params={"query": "x" * 2001}).status_code == 413


def test_chat_without_documents_says_so(client):
    body = client.post("/chat/", params={"query": "anything?"}).json()
    assert body["sources"] == [] and "could not find" in body["response"]


def test_oversized_uploads_are_rejected(settings):
    from dataclasses import replace

    from fastapi.testclient import TestClient

    from main import create_app

    with TestClient(create_app(replace(settings, max_upload_mb=0))) as small:
        result = small.post("/upload/", files={"file": ("a.txt", b"hello", "text/plain")}).json()
    assert result["status"] == "Failed" and "larger than" in result["message"]
