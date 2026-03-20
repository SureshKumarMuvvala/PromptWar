"""
Emergency assessment API routes.
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import rate_limiter
from app.models.schemas import (
    AssessResponse,
    ValidateRequest,
    ValidateResponse,
    ActionsRequest,
    RecommendedAction,
)
from app.services.gemini_client import GeminiClient
from app.services.ingestion import IngestionService
from app.services.structuring import StructuringService
from app.services.rag_validator import RAGValidator
from app.services.action_generator import ActionGenerator
from app.utils.exceptions import NoInputProvidedError, GeminiAPIError
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/emergency", tags=["Emergency"])

# ── Shared service instances (created once, reused) ──────────────────────────
_gemini_client: Optional[GeminiClient] = None
_rag_validator: Optional[RAGValidator] = None
_action_generator = ActionGenerator()


def get_gemini() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


def get_rag_validator() -> RAGValidator:
    global _rag_validator
    if _rag_validator is None:
        _rag_validator = RAGValidator(get_gemini())
        _rag_validator.load_index()
    return _rag_validator


# ── POST /emergency/assess ───────────────────────────────────────────────────


@router.post("/assess", response_model=AssessResponse, dependencies=[Depends(rate_limiter)])
async def assess_emergency(
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
):
    """
    Accept multimodal emergency input and return a structured, validated
    triage assessment with recommended actions.
    """
    # Validate at least one input is provided
    has_text = text and text.strip()
    has_audio = audio and audio.filename
    has_image = image and image.filename
    if not (has_text or has_audio or has_image):
        raise NoInputProvidedError()

    gemini = get_gemini()
    ingestion = IngestionService(gemini)

    # ── Step 1: Ingest multimodal input ──────────────────────────
    audio_bytes = None
    audio_mime = None
    image_bytes = None
    image_mime = None

    if has_audio:
        audio_bytes = await audio.read()
        audio_mime = audio.content_type or "audio/webm"

    if has_image:
        image_bytes = await image.read()
        image_mime = image.content_type or "image/jpeg"

    try:
        context = await ingestion.process(
            text=text,
            audio_bytes=audio_bytes,
            audio_mime=audio_mime,
            image_bytes=image_bytes,
            image_mime=image_mime,
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise GeminiAPIError(f"Failed to process input: {str(e)}")

    # ── Step 2: Structure via Gemini ─────────────────────────────
    structuring = StructuringService(gemini)
    try:
        assessment = await structuring.structure(context["unified_text"])
    except Exception as e:
        logger.error(f"Structuring failed: {e}")
        raise GeminiAPIError(f"Failed to structure assessment: {str(e)}")

    # ── Step 3: RAG validation ───────────────────────────────────
    rag = get_rag_validator()
    validation = await rag.validate(assessment)

    # ── Step 4: Generate actions ─────────────────────────────────
    location = None
    if latitude is not None and longitude is not None:
        location = {"latitude": latitude, "longitude": longitude}

    actions = _action_generator.generate(
        assessment=assessment,
        validation=validation,
        location=location,
    )

    return AssessResponse(
        input_summary=context["unified_text"][:500],
        structured_assessment=assessment,
        rag_validation=validation,
        recommended_actions=actions,
    )


# ── POST /emergency/validate ────────────────────────────────────────────────


@router.post("/validate", response_model=ValidateResponse, dependencies=[Depends(rate_limiter)])
async def validate_assessment(request: ValidateRequest):
    """Validate a pre-structured assessment against the RAG knowledge base."""
    rag = get_rag_validator()
    validation = await rag.validate(request.structured_assessment)
    return ValidateResponse(
        validated=validation.validated,
        matched_protocols=validation.matched_protocols,
        confidence_score=validation.confidence_score,
        corrections=validation.corrections,
    )


# ── POST /emergency/actions ─────────────────────────────────────────────────


@router.post("/actions", response_model=list[RecommendedAction], dependencies=[Depends(rate_limiter)])
async def generate_actions(request: ActionsRequest):
    """Generate recommended actions from a validated assessment."""
    actions = _action_generator.generate(
        assessment=request.structured_assessment,
        validation=request.rag_validation,
        location=request.location,
    )
    return actions
