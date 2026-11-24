"""ChatPDFGio API: upload documents and ask questions answered from their content."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.config import Settings
from app.extraction import EmptyDocument, UnsupportedFileType
from app.rag import RagService
from app.services import build_service

logger = logging.getLogger("chatpdfgio")


class UploadResult(BaseModel):
    filename: str
    status: str
    message: str
    chunks: int = 0


class MultipleUploadResponse(BaseModel):
    results: list[UploadResult]


class SourceOut(BaseModel):
    source: str
    location: str
    score: float


class ChatResponse(BaseModel):
    response: str
    sources: list[SourceOut] = []


class StatusResponse(BaseModel):
    status: str
    message: str
    backend: str


def get_service(request: Request) -> RagService:
    return request.app.state.service


ServiceDep = Annotated[RagService, Depends(get_service)]


def create_app(settings: Settings | None = None, service: RagService | None = None) -> FastAPI:
    """Application factory. Tests pass their own settings and service."""
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # External clients are created at startup, not at import time.
        app.state.settings = settings
        app.state.service = service or build_service(settings)
        logger.info("ChatPDFGio started with the %s backend", settings.backend)
        yield

    app = FastAPI(title="ChatPDFGio", version="2.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    async def _ingest(service: RagService, file: UploadFile) -> UploadResult:
        name = file.filename or "document"
        data = await file.read()
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            return UploadResult(
                filename=name,
                status="Failed",
                message=f"file is larger than {settings.max_upload_mb} MB",
            )
        try:
            result = service.ingest(name, data)
        except (UnsupportedFileType, EmptyDocument) as error:
            return UploadResult(filename=name, status="Failed", message=str(error))
        except Exception:
            # Details go to the log; the client gets a neutral message.
            logger.exception("failed to process %s", name)
            return UploadResult(
                filename=name, status="Failed", message="the file could not be processed"
            )
        return UploadResult(
            filename=result.filename,
            status="Success",
            message="File uploaded, processed and indexed",
            chunks=result.chunks,
        )

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get("/health", tags=["Status"])
    def health() -> dict[str, str]:
        return {"status": "ok", "backend": settings.backend}

    @app.get("/check-documents/", tags=["Documents"])
    def check_documents(service: ServiceDep) -> StatusResponse:
        loaded = service.has_documents()
        return StatusResponse(
            status="Success",
            message="Documents loaded." if loaded else "No documents loaded.",
            backend=settings.backend,
        )

    @app.post("/upload/", tags=["Documents"])
    async def upload(service: ServiceDep, file: UploadFile = File(...)) -> UploadResult:
        """Upload one file, extract its text and index it."""
        return await _ingest(service, file)

    @app.post("/multipleupload/", tags=["Documents"])
    async def multiple_upload(
        service: ServiceDep, files: list[UploadFile] = File(...)
    ) -> MultipleUploadResponse:
        """Upload several files (PDF, DOCX, PPTX, TXT, MD; MP3/M4A/WAV on the cloud backend)."""
        return MultipleUploadResponse(results=[await _ingest(service, file) for file in files])

    @app.post("/chat/", tags=["Chat"])
    def chat(
        service: ServiceDep,
        query: str = Query(..., min_length=1, description="The question to answer"),
    ) -> ChatResponse:
        """Answer a question using only the content of the indexed documents."""
        if len(query) > settings.max_query_chars:
            raise HTTPException(
                status_code=413,
                detail=f"the question is longer than {settings.max_query_chars} characters",
            )
        try:
            answer = service.answer(query)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except Exception as error:
            logger.exception("failed to answer a question")
            raise HTTPException(
                status_code=502, detail="the answer could not be generated"
            ) from error
        return ChatResponse(
            response=answer.text,
            sources=[SourceOut(**vars(source)) for source in answer.sources],
        )

    return app


app = create_app()
