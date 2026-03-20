"""
Multimodal ingestion — preprocesses text, audio, and image inputs
into a unified context string for Gemini.
"""

from typing import Optional
from fastapi import UploadFile

from app.services.gemini_client import GeminiClient
from app.utils.logger import get_logger
from app.utils.exceptions import ValidationError

logger = get_logger(__name__)


class IngestionService:
    """Preprocesses multimodal input into unified text context."""

    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client

    # ── Security Constraints ─────────────────────────────────────
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_AUDIO = {"audio/mpeg", "audio/wav", "audio/webm", "audio/ogg", "audio/mp4"}
    ALLOWED_IMAGES = {"image/jpeg", "image/png", "image/webp", "image/heic"}

    async def _validate_file(self, file: UploadFile, allowed_types: set[str]):
        """Strict validation of file size and MIME type."""
        if file.content_type not in allowed_types:
            raise ValidationError(
                detail=f"Unsupported file type: {file.content_type}. Allowed: {allowed_types}"
            )
        
        # Check size by seeking to the end
        current_pos = file.file.tell()
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(current_pos)
        
        if size > self.MAX_FILE_SIZE:
            raise ValidationError(
                detail=f"File too large: {size/1024/1024:.1f}MB. Max: {self.MAX_FILE_SIZE/1024/1024}MB"
            )

    async def ingest_multimodal(
        self,
        text: Optional[str] = None,
        audio: Optional[UploadFile] = None,
        image: Optional[UploadFile] = None,
    ) -> dict:
        """
        Process all input modalities and return a unified context.

        Returns:
            {
                "unified_text": str,
                "image_bytes": bytes|None,
                "image_mime": str|None,
                "sources": list[str],
            }
        """
        contexts = []
        sources = []
        image_data = None
        image_data_mime = None

        # ── Text input ───────────────────────────────────────────
        if text and text.strip():
            cleaned = text.strip()
            contexts.append(f"[Patient Description]: {cleaned}")
            sources.append("TEXT")
            logger.info(f"Text input received: {len(cleaned)} chars")

        # ── Audio input ──────────────────────────────────────────
        if audio:
            await self._validate_file(audio, self.ALLOWED_AUDIO)
            logger.info(f"Processing audio input: {audio.filename}")
            try:
                audio_bytes = await audio.read()
                transcription = await self.gemini.transcribe_audio(
                    audio_bytes, mime_type=audio.content_type
                )
                contexts.append(f"[Voice Transcription]: {transcription}")
                sources.append("AUDIO")
                logger.info(f"Audio transcription success: {len(transcription)} chars")
            except Exception as e:
                logger.error(f"Audio transcription failed: {e}")
                contexts.append("[Voice Transcription]: (transcription failed)")

        # ── Image input ──────────────────────────────────────────
        if image:
            await self._validate_file(image, self.ALLOWED_IMAGES)
            logger.info(f"Processing image input: {image.filename}")
            try:
                image_data = await image.read()
                image_data_mime = image.content_type
                description = await self.gemini.describe_image(
                    image_data, mime_type=image_data_mime
                )
                contexts.append(f"[Image Analysis]: {description}")
                sources.append("IMAGE")
                logger.info(f"Image description success: {len(description)} chars")
            except Exception as e:
                logger.error(f"Image description failed: {e}")
                image_data = None
                image_data_mime = None

        unified = "\n\n".join(contexts) if contexts else ""
        return {
            "unified_text": unified,
            "image_bytes": image_data,
            "image_mime": image_data_mime,
            "sources": sources,
        }
