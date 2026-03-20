"""
Gemini API client — handles multimodal generation and structured output.
"""

import logging
import json
from typing import Optional, TypeVar, Type

import google.generativeai as genai
from pydantic import BaseModel

from app.config import get_settings
from app.utils.logger import get_logger
from app.utils.exceptions import GeminiAPIError

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    """
    Client for interacting with Google Gemini API models.
    Supports multimodal inputs including text, audio, and images.
    """

    def __init__(self):
        """Initializes the Gemini client using settings from config."""
        self.settings = get_settings()
        genai.configure(api_key=self.settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(self.settings.GEMINI_MODEL)
        self.embedding_model = self.settings.GEMINI_EMBEDDING_MODEL
        self.max_retries = self.settings.GEMINI_MAX_RETRIES
        self.timeout = self.settings.GEMINI_TIMEOUT

    async def generate_structured_response(
        self, 
        prompt: str, 
        response_schema: Type[T]
    ) -> T:
        """
        Generate a structured response from Gemini using a Pydantic schema.

        Args:
            prompt: The instruction prompt for Gemini.
            response_schema: The Pydantic model class to use for validation.

        Returns:
            An instance of the response_schema populated with model output.

        Raises:
            GeminiAPIError: If the model fails to return a valid response.
        """
        logger.info(f"Generating structured response (schema: {response_schema.__name__})")
        
        try:
            # We use the 'response_mime_type' and 'response_schema' parameters 
            # for native structured output if supported by the model version.
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema
                )
            )
            
            if not response.text:
                raise GeminiAPIError("Empty response from Gemini")
                
            return response_schema.model_validate_json(response.text)
            
        except Exception as e:
            logger.error(f"Gemini structured generation failed: {e}")
            raise GeminiAPIError(f"Failed to generate structured response: {str(e)}")

    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str) -> str:
        """
        Transcribe audio content using Gemini's multimodal capabilities.

        Args:
            audio_bytes: The raw audio file bytes.
            mime_type: The MIME type of the audio (e.g., 'audio/wav').

        Returns:
            The transcribed text.
        """
        logger.info(f"Transcribing audio ({len(audio_bytes)} bytes)")
        try:
            response = self.model.generate_content([
                "Please transcribe the following audio recording verbatim.",
                {"mime_type": mime_type, "data": audio_bytes}
            ])
            return response.text
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            raise GeminiAPIError(f"Audio transcription failed: {str(e)}")

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str:
        """
        Generate a clinical description of an image.

        Args:
            image_bytes: The raw image bytes.
            mime_type: The MIME type of the image (e.g., 'image/jpeg').

        Returns:
            A descriptive text analysis of the image.
        """
        logger.info(f"Analyzing image ({len(image_bytes)} bytes)")
        try:
            response = self.model.generate_content([
                "Describe the medical situation shown in this image. Focus on visible injuries, symptoms, or environmental hazards.",
                {"mime_type": mime_type, "data": image_bytes}
            ])
            return response.text
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise GeminiAPIError(f"Image analysis failed: {str(e)}")

    async def get_embeddings(self, text: str) -> list[float]:
        """
        Generate vector embeddings for a given text string.

        Args:
            text: The input text string.

        Returns:
            A list of floats representing the embedding vector.
        """
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise GeminiAPIError(f"Failed to generate embeddings: {str(e)}")
