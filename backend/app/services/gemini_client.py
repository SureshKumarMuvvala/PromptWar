"""
Google Gemini API wrapper with retry logic and structured output.
"""

import json
import asyncio
from typing import Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """Async-safe wrapper around the Google Gemini SDK."""

    def __init__(self):
        settings = get_settings()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.embedding_model = settings.GEMINI_EMBEDDING_MODEL
        self.max_retries = settings.GEMINI_MAX_RETRIES
        self.timeout = settings.GEMINI_TIMEOUT

    async def generate_structured(
        self,
        prompt: str,
        parts: Optional[list] = None,
        response_schema: Optional[dict] = None,
    ) -> dict:
        """
        Send a multimodal prompt to Gemini and parse the JSON response.

        Args:
            prompt: The text prompt / system instruction.
            parts: Additional content parts (images, audio, etc.).
            response_schema: If provided, passed to Gemini's structured output mode.

        Returns:
            Parsed JSON dict from Gemini's response.
        """
        content = [prompt]
        if parts:
            content.extend(parts)

        generation_config = GenerationConfig(
            temperature=0.2,
            response_mime_type="application/json",
        )

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Gemini API call attempt {attempt}/{self.max_retries}")
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    content,
                    generation_config=generation_config,
                )
                text = response.text.strip()
                # Remove markdown code fences if present
                if text.startswith("```"):
                    text = text.split("\n", 1)[1]
                    if text.endswith("```"):
                        text = text[:-3].strip()
                return json.loads(text)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {e}")
                if attempt == self.max_retries:
                    raise
            except Exception as e:
                logger.error(f"Gemini API error (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(2 ** attempt)

        return {}

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for a text string."""
        result = await asyncio.to_thread(
            genai.embed_content,
            model=f"models/{self.embedding_model}",
            content=text,
            task_type="retrieval_document",
        )
        return result["embedding"]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        tasks = [self.embed_text(t) for t in texts]
        return await asyncio.gather(*tasks)

    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str) -> str:
        """Transcribe audio using Gemini's multimodal capability."""
        prompt = (
            "Transcribe the following audio recording accurately. "
            "The audio describes a medical emergency. "
            "Return ONLY the transcription text, no additional commentary."
        )
        audio_part = {"mime_type": mime_type, "data": audio_bytes}
        response = await asyncio.to_thread(
            self.model.generate_content,
            [prompt, audio_part],
        )
        return response.text.strip()

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str:
        """Describe a medical/injury image using Gemini Vision."""
        prompt = (
            "You are a medical triage assistant. Describe the medical condition "
            "visible in this image in clinical terms. Note any visible injuries, "
            "burns, rashes, swelling, bleeding, or other abnormalities. "
            "Be specific about location, severity, and approximate size."
        )
        image_part = {"mime_type": mime_type, "data": image_bytes}
        response = await asyncio.to_thread(
            self.model.generate_content,
            [prompt, image_part],
        )
        return response.text.strip()
