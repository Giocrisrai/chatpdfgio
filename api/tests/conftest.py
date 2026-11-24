"""Test setup: every test runs on the local backend, with no network and no API keys."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))


def make_pdf(pages: list[str]) -> bytes:
    """Build a small, valid, text-only PDF with one string per page."""
    objects: list[bytes] = []

    def add(body: str) -> int:
        objects.append(body.encode("latin-1"))
        return len(objects)

    font = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids = []
    pages_id = len(pages) * 2 + 2  # the /Pages object comes after contents and pages
    for text in pages:
        escaped = text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET"
        content = add(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
        page_ids.append(
            add(
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content} 0 R /Resources << /Font << /F1 {font} 0 R >> >> >>"
            )
        )
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    assert add(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>") == pages_id
    catalog = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>")

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets:
        out.write(f"{offset:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog} 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode()
    )
    return out.getvalue()


@pytest.fixture
def pdf_factory():
    return make_pdf


@pytest.fixture
def settings(tmp_path):
    from app.config import Settings

    return Settings(backend="local", documents_dir=str(tmp_path / "documents"))


@pytest.fixture
def client(settings):
    from fastapi.testclient import TestClient

    from main import create_app

    with TestClient(create_app(settings)) as test_client:
        yield test_client
