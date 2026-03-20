"""
Emergency assessment API routes.
"""

import time
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
from app.services.google_maps import GoogleMapsService
from app.services.monitoring import monitor
from app.services.structuring import STRUCTURING_PROMPT
from app.utils.exceptions import NoInputProvidedError, GeminiAPIError
from app.utils.logger import get_logger
from app.config import get_settings

logger = get_logger(__name__)

router = APIRouter(prefix="/emergency", tags=["Emergency"])

# ── Shared service instances (created once, reused) ──────────────────────────
_gemini_client: Optional[GeminiClient] = None
_rag_validator: Optional[RAGValidator] = None
_action_generator = ActionGenerator()
_maps_service = GoogleMapsService()


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
    start_time = time.time()
    settings = get_settings()
    # Validate at least one input is provided
    has_text = text and text.strip()
    has_audio = audio and audio.filename
    has_image = image and image.filename
    if not (has_text or has_audio or has_image):
        raise NoInputProvidedError()

    gemini = get_gemini()
    ingestion = IngestionService(gemini)

    # ── Step 1: Ingest multimodal input ──────────────────────────
    try:
        context = await ingestion.ingest_multimodal(
            text=text,
            audio=audio,
            image=image,
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        if "ValidationError" in str(type(e)):
             raise e
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
    hospitals = []
    if latitude is not None and longitude is not None:
        location = {"latitude": latitude, "longitude": longitude}
        # Fetch real hospitals for the assessment response
        hospitals = await _maps_service.search_nearby_hospitals(
            lat=latitude, 
            lng=longitude
        )

    actions = _action_generator.generate(
        assessment=assessment,
        validation=validation,
        location=location,
        hospitals=hospitals,
    )

    # ── Step 5: Monitoring & Debug ───────────────────────────────
    latency_ms = (time.time() - start_time) * 1000
    
    response = AssessResponse(
        input_summary=context["unified_text"][:500],
        structured_assessment=assessment,
        rag_validation=validation,
        recommended_actions=actions,
    )

    if settings.DEBUG:
        response.debug_info = {
            "prompt": STRUCTURING_PROMPT.format(context=context["unified_text"]),
            "latency_ms": round(latency_ms, 2),
            "model": settings.GEMINI_MODEL,
        }

    monitor.log_assessment_telemetry(
        request_id=response.request_id,
        latency_ms=latency_ms,
        confidence=validation.confidence_score,
        severity=assessment.severity.value
    )

    return response


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
