"""
Custom HTTP exceptions for the application.
"""

from fastapi import HTTPException, status


class NoInputProvidedError(HTTPException):
    """Raised when no input (text, audio, or image) is provided."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one input must be provided: text, audio, or image.",
        )


class GeminiAPIError(HTTPException):
    """Raised when the Gemini API call fails."""

    def __init__(self, detail: str = "Gemini API request failed."):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        )


class RAGIndexNotLoadedError(HTTPException):
    """Raised when FAISS index is not available."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG knowledge base index is not loaded. Service is degraded.",
        )


class RateLimitExceededError(HTTPException):
    """Raised when rate limit is exceeded."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )


class ValidationError(HTTPException):
    """Raised when input data fails validation (size, type, etc)."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class InvalidAPIKeyError(HTTPException):
    """Raised when an invalid or missing API key is provided."""

    def __init__(self, detail: str = "Invalid or missing API key"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )
