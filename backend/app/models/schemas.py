"""
Pydantic models for request / response validation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from .enums import Severity, TriageLevel, ActionType


# ── Sub-models ───────────────────────────────────────────────────────────────


class PossibleCondition(BaseModel):
    """A possible medical condition with ICD-10 code."""
    name: str = Field(..., examples=["Myocardial Infarction"])
    icd10: str = Field(..., examples=["I21.9"])
    confidence: float = Field(..., ge=0, le=1, examples=[0.87])


class VitalSignsMentioned(BaseModel):
    """Any vital signs or pain scales mentioned in the input."""
    pain_scale: Optional[int] = Field(None, ge=0, le=10)
    heart_rate: Optional[int] = None
    blood_pressure: Optional[str] = None
    temperature_c: Optional[float] = None
    spo2_percent: Optional[int] = None


class StructuredAssessment(BaseModel):
    """Structured emergency assessment produced by Gemini."""
    chief_complaint: str = Field(..., examples=["Chest pain"])
    symptoms: list[str] = Field(default_factory=list)
    severity: Severity = Severity.MODERATE
    triage_level: TriageLevel = TriageLevel.YELLOW
    possible_conditions: list[PossibleCondition] = Field(default_factory=list)
    vital_signs_mentioned: Optional[VitalSignsMentioned] = None
    patient_age: Optional[str] = None
    patient_gender: Optional[str] = None
    additional_context: Optional[str] = None


class RAGCorrection(BaseModel):
    """A single field correction suggested by RAG validation."""
    field: str
    original: str
    corrected: str
    reason: str


class RAGValidation(BaseModel):
    """Result of RAG-based clinical validation."""
    validated: bool = True
    matched_protocols: list[str] = Field(default_factory=list)
    confidence_score: float = Field(0.0, ge=0, le=1)
    corrections: list[RAGCorrection] = Field(default_factory=list)


class HospitalInfo(BaseModel):
    """Information about a nearby hospital."""
    name: str
    address: Optional[str] = None
    distance_km: Optional[float] = None
    eta_min: Optional[int] = None
    rating: Optional[float] = None
    phone: Optional[str] = None
    has_emergency: bool = True
    location: Optional[dict] = None  # {"lat": ..., "lng": ...}


class RecommendedAction(BaseModel):
    """A recommended emergency action."""
    type: ActionType
    priority: int = Field(..., ge=1)
    description: str
    auto_triggered: bool = False
    hospitals: Optional[list[HospitalInfo]] = None


# ── Request Models ───────────────────────────────────────────────────────────


class ValidateRequest(BaseModel):
    """Request body for /validate endpoint."""
    structured_assessment: StructuredAssessment


class ActionsRequest(BaseModel):
    """Request body for /actions endpoint."""
    structured_assessment: StructuredAssessment
    rag_validation: Optional[RAGValidation] = None
    location: Optional[dict] = None  # {"latitude": ..., "longitude": ...}


# ── Response Models ──────────────────────────────────────────────────────────


class AssessResponse(BaseModel):
    """Full response for /assess endpoint."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    input_summary: str = ""
    structured_assessment: StructuredAssessment
    rag_validation: RAGValidation
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    debug_info: Optional[dict] = None  # Raw prompts, response times, model version


class ValidateResponse(BaseModel):
    """Response for /validate endpoint."""
    validated: bool
    matched_protocols: list[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    corrections: list[RAGCorrection] = Field(default_factory=list)


class HospitalSearchResponse(BaseModel):
    """Response for /hospitals endpoint."""
    hospitals: list[HospitalInfo] = Field(default_factory=list)


class HealthCheckResponse(BaseModel):
    """Response for /status endpoint."""
    status: str = "healthy"
    version: str = "1.0.0"
    faiss_index_loaded: bool = False
