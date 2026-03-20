"""
Structuring service — converts unstructured emergency context into a StructuredAssessment.
"""

from app.models.schemas import StructuredAssessment
from app.services.gemini_client import GeminiClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

STRUCTURING_PROMPT = """
You are a senior emergency triage physician.
Based on the following patient description (which may include voice transcriptions and image analyses), 
extract a structured medical assessment.

[CONTEXT]
{context}

[INSTRUCTIONS]
1. Identify the chief complaint (primary reason for emergency).
2. List all observed or reported symptoms.
3. Categorize the severity (CRITICAL, HIGH, MODERATE, LOW).
4. Assign a triage level (RED, ORANGE, YELLOW, GREEN, BLUE).
5. Suggest possible conditions with ICD-10 codes and confidence scores.
6. Extract mentions of vital signs (pain scale 0-10, HR, BP, Temp, SpO2).
7. Extract patient age and gender if mentioned.

Ensure the output is strictly valid according to the schema.
"""

class StructuringService:
    """
    Service for converting unstructured emergency text into a structured schema
    using Gemini Pro's reasoning capabilities.
    """

    def __init__(self, gemini_client: GeminiClient):
        """
        Initializes the service with a Gemini client.

        Args:
            gemini_client: An instance of GeminiClient.
        """
        self.gemini = gemini_client

    async def structure(self, context: str) -> StructuredAssessment:
        """
        Parse unstructured emergency context into a StructuredAssessment model.

        Args:
            context: The raw multimodal context string.

        Returns:
            A StructuredAssessment object containing chief complaint, severity, etc.
        """
        logger.info("Structuring emergency context...")
        
        prompt = STRUCTURING_PROMPT.format(context=context)
        
        assessment = await self.gemini.generate_structured_response(
            prompt=prompt,
            response_schema=StructuredAssessment
        )
        
        logger.info(f"Structuring complete: {assessment.chief_complaint} ({assessment.severity})")
        return assessment
