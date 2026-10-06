"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.summarize import router as summarize_router
from app.api.chat import router as chat_router
from app.core.config import get_settings
from app.db.session import engine, initialize_database
from app.services.vector_store import vector_store

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await initialize_database()
    vector_store.initialize()
    # Ensure upload directory exists
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    yield
    await engine.dispose()


app = FastAPI(
    title="Document Summarizer API",
    version="0.2.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/api/health", tags=["health"])
app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(summarize_router, prefix="/api/documents", tags=["summarize"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
