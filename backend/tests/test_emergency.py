"""
Tests for the emergency assessment endpoint.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import StructuredAssessment, RAGValidation
from app.models.enums import Severity, TriageLevel


client = TestClient(app)


class TestHealthCheck:
    """Tests for the /status endpoint."""

    def test_health_check_returns_200(self):
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "faiss_index_loaded" in data


class TestAssessEndpoint:
    """Tests for the /assess endpoint."""

    def test_no_input_returns_400(self):
        """Should return 400 when no input is provided."""
        response = client.post("/api/v1/emergency/assess")
        assert response.status_code == 400

    @patch("app.api.v1.emergency.get_gemini")
    @patch("app.api.v1.emergency.get_rag_validator")
    def test_text_input_returns_assessment(self, mock_rag, mock_gemini):
        """Should process text input and return a structured assessment."""
        # Mock Gemini client
        mock_gemini_instance = MagicMock()
        mock_gemini_instance.generate_structured = AsyncMock(
            return_value={
                "chief_complaint": "Chest pain",
                "symptoms": ["chest_pain", "shortness_of_breath"],
                "severity": "HIGH",
                "triage_level": "ORANGE",
                "possible_conditions": [
                    {"name": "Angina", "icd10": "I20.9", "confidence": 0.7}
                ],
                "vital_signs_mentioned": None,
                "patient_age": None,
                "patient_gender": None,
                "additional_context": None,
            }
        )
        mock_gemini.return_value = mock_gemini_instance

        # Mock RAG validator
        mock_rag_instance = MagicMock()
        mock_rag_instance.validate = AsyncMock(
            return_value=RAGValidation(
                validated=True,
                matched_protocols=["ACS_PROTOCOL_001"],
                confidence_score=0.85,
                corrections=[],
            )
        )
        mock_rag.return_value = mock_rag_instance

        response = client.post(
            "/api/v1/emergency/assess",
            data={"text": "I have severe chest pain and difficulty breathing"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "structured_assessment" in data
        assert "rag_validation" in data
        assert "recommended_actions" in data


class TestValidateEndpoint:
    """Tests for the /validate endpoint."""

    @patch("app.api.v1.emergency.get_rag_validator")
    def test_validate_returns_result(self, mock_rag):
        """Should validate a structured assessment."""
        mock_rag_instance = MagicMock()
        mock_rag_instance.validate = AsyncMock(
            return_value=RAGValidation(
                validated=True,
                matched_protocols=["BURN_PROTOCOL_005"],
                confidence_score=0.9,
                corrections=[],
            )
        )
        mock_rag.return_value = mock_rag_instance

        response = client.post(
            "/api/v1/emergency/validate",
            json={
                "structured_assessment": {
                    "chief_complaint": "Burn injury",
                    "symptoms": ["burn_injury", "pain"],
                    "severity": "HIGH",
                    "triage_level": "ORANGE",
                    "possible_conditions": [],
                }
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["validated"] is True
