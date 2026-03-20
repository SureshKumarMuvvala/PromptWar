"""
Multimodal ingestion — preprocesses text, audio, and image inputs
into a unified context string for Gemini.
"""

from typing import Optional

from app.services.gemini_client import GeminiClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class IngestionService:
    """Preprocesses multimodal input into unified text context."""

    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client

    async def process(
        self,
        text: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        audio_mime: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_mime: Optional[str] = None,
    ) -> dict:
        """
        Process all input modalities and return a unified context.

        Returns:
            {
                "unified_text": str,       # Combined text from all sources
                "image_bytes": bytes|None,  # Raw image for Gemini Vision
                "image_mime": str|None,
                "sources": list[str],       # Which modalities were used
            }
        """
        parts = []
        sources = []

        # ── Text input ───────────────────────────────────────────
        if text and text.strip():
            cleaned = text.strip()
            parts.append(f"[Patient Description]: {cleaned}")
            sources.append("TEXT")
            logger.info(f"Text input received: {len(cleaned)} chars")

        # ── Audio input ──────────────────────────────────────────
        if audio_bytes:
            mime = audio_mime or "audio/webm"
            logger.info(f"Transcribing audio ({len(audio_bytes)} bytes, {mime})")
            try:
                transcription = await self.gemini.transcribe_audio(audio_bytes, mime)
                parts.append(f"[Voice Transcription]: {transcription}")
                sources.append("AUDIO")
                logger.info(f"Audio transcription: {transcription[:100]}...")
            except Exception as e:
                logger.error(f"Audio transcription failed: {e}")
                parts.append("[Voice Transcription]: (transcription failed)")

        # ── Image input ──────────────────────────────────────────
        image_data = None
        image_data_mime = None
        if image_bytes:
            mime = image_mime or "image/jpeg"
            logger.info(f"Describing image ({len(image_bytes)} bytes, {mime})")
            try:
                description = await self.gemini.describe_image(image_bytes, mime)
                parts.append(f"[Image Analysis]: {description}")
                sources.append("IMAGE")
                image_data = image_bytes
                image_data_mime = mime
                logger.info(f"Image description: {description[:100]}...")
            except Exception as e:
                logger.error(f"Image description failed: {e}")

        unified = "\n\n".join(parts) if parts else ""
        return {
            "unified_text": unified,
            "image_bytes": image_data,
            "image_mime": image_data_mime,
            "sources": sources,
        }
