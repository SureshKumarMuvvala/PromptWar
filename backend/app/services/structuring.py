"""
Structuring engine — converts unstructured emergency descriptions
into structured JSON via Gemini with a carefully crafted prompt.
"""

from app.models.schemas import StructuredAssessment
from app.services.gemini_client import GeminiClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

STRUCTURING_PROMPT = """You are an expert emergency medical triage AI assistant.

Given the following emergency information from a patient, produce a **structured JSON assessment**.

## Input
{context}

## Instructions
1. Identify the **chief complaint** (the main reason for the emergency).
2. Extract all **symptoms** as a list of short clinical terms (snake_case).
3. Determine the **severity** — one of: CRITICAL, HIGH, MODERATE, LOW.
   - CRITICAL: Life-threatening, needs immediate intervention (cardiac arrest, severe hemorrhage, stroke, anaphylaxis).
   - HIGH: Serious, needs emergency department (fractures, deep wounds, severe pain, difficulty breathing).
   - MODERATE: Needs prompt medical attention (sprains, moderate burns, persistent vomiting).
   - LOW: Can be managed with self-care or scheduled visit (minor cuts, mild cold symptoms).
4. Assign a **triage_level** color — RED (immediate), ORANGE (very urgent), YELLOW (urgent), GREEN (standard), BLUE (non-urgent).
5. List **possible_conditions** with ICD-10 codes and confidence (0-1).
6. Extract any **vital signs** mentioned (pain scale, heart rate, blood pressure, temperature, SpO2).
7. Note **patient age** and **gender** if mentioned.
8. Add any **additional context** that's clinically relevant.

## Output JSON Schema
{{
  "chief_complaint": "string",
  "symptoms": ["string"],
  "severity": "CRITICAL|HIGH|MODERATE|LOW",
  "triage_level": "RED|ORANGE|YELLOW|GREEN|BLUE",
  "possible_conditions": [
    {{"name": "string", "icd10": "string", "confidence": 0.0}}
  ],
  "vital_signs_mentioned": {{
    "pain_scale": null,
    "heart_rate": null,
    "blood_pressure": null,
    "temperature_c": null,
    "spo2_percent": null
  }},
  "patient_age": null,
  "patient_gender": null,
  "additional_context": null
}}

Respond with ONLY the JSON object, no markdown or explanation."""


class StructuringService:
    """Converts unstructured multimodal context into structured assessment."""

    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client

    async def structure(self, context: str) -> StructuredAssessment:
        """
        Send the unified context to Gemini and parse into StructuredAssessment.

        Args:
            context: Unified text from the ingestion service.

        Returns:
            Validated StructuredAssessment Pydantic model.
        """
        prompt = STRUCTURING_PROMPT.format(context=context)
        logger.info("Sending structuring prompt to Gemini")

        raw = await self.gemini.generate_structured(prompt)
        logger.info(f"Gemini returned structured assessment: {raw.get('chief_complaint', 'N/A')}")

        # Validate through Pydantic
        assessment = StructuredAssessment(**raw)
        return assessment
