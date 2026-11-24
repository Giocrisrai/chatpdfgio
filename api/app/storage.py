"""Where the original uploaded files are kept: a local folder or an S3 bucket."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_name(filename: str) -> str:
    """Reduce a client-supplied file name to a safe base name (no path traversal)."""
    base = Path(filename.replace("\\", "/")).name
    cleaned = _UNSAFE.sub("_", base).strip("._")
    return cleaned or "document"


class DocumentStorage(Protocol):
    def save(self, filename: str, data: bytes) -> str: ...

    def has_documents(self) -> bool: ...


class LocalStorage:
    def __init__(self, directory: str) -> None:
        self._directory = Path(directory)

    def save(self, filename: str, data: bytes) -> str:
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._directory / safe_name(filename)
        path.write_bytes(data)
        return str(path)

    def has_documents(self) -> bool:
        return self._directory.is_dir() and any(self._directory.iterdir())


class S3Storage:
    def __init__(self, client, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def save(self, filename: str, data: bytes) -> str:
        key = safe_name(filename)
        self._client.put_object(Body=data, Bucket=self._bucket, Key=key)
        return f"s3://{self._bucket}/{key}"

    def has_documents(self) -> bool:
        response = self._client.list_objects_v2(Bucket=self._bucket, MaxKeys=1)
        return response.get("KeyCount", 0) > 0
