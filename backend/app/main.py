"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1.router import router as v1_router
from app.models.schemas import HealthCheckResponse
from app.services.rag_validator import RAGValidator
from app.services.gemini_client import GeminiClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Track FAISS index state ──────────────────────────────────────────────────
_faiss_loaded = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    global _faiss_loaded
    logger.info("Starting Emergency Health Assistant...")

    # Attempt to load FAISS index at startup
    try:
        gemini = GeminiClient()
        rag = RAGValidator(gemini)
        _faiss_loaded = rag.load_index()
        
        if not _faiss_loaded:
            logger.info("FAISS index not found. Building index...")
            from app.rag.indexer import build_index
            await build_index()
            # Attempt to reload after building
            _faiss_loaded = rag.load_index()

        if _faiss_loaded:
            logger.info("FAISS index loaded successfully at startup")
        else:
            logger.warning("FAISS index not available — RAG validation will be degraded")
    except Exception as e:
        logger.error(f"Failed to load/build FAISS index: {e}")
        _faiss_loaded = False

    yield

    logger.info("Shutting down Emergency Health Assistant...")


# ── App factory ──────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-ready Emergency Health Assistant API. "
            "Accepts multimodal input (text, voice, image), performs AI-powered "
            "triage assessment, validates against medical protocols via RAG, and "
            "generates real-world emergency actions."
        ),
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────
    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ───────────────────────────────────────────────────
    app.include_router(v1_router)

    @app.get("/api/v1/status", response_model=HealthCheckResponse, tags=["Health"])
    async def health_check():
        return HealthCheckResponse(
            status="healthy",
            version=settings.APP_VERSION,
            faiss_index_loaded=_faiss_loaded,
        )

    return app


app = create_app()
