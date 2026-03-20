"""
Tests for the structuring service.
"""

import pytest
from app.models.schemas import StructuredAssessment
from app.models.enums import Severity, TriageLevel


class TestStructuredAssessmentModel:
    """Validate the StructuredAssessment Pydantic model."""

    def test_valid_assessment(self):
        """Should create a valid assessment from correct data."""
        data = {
            "chief_complaint": "Chest pain",
            "symptoms": ["chest_pain", "diaphoresis"],
            "severity": "CRITICAL",
            "triage_level": "RED",
            "possible_conditions": [
                {"name": "MI", "icd10": "I21.9", "confidence": 0.9}
            ],
        }
        assessment = StructuredAssessment(**data)
        assert assessment.chief_complaint == "Chest pain"
        assert assessment.severity == Severity.CRITICAL
        assert assessment.triage_level == TriageLevel.RED
        assert len(assessment.possible_conditions) == 1
        assert assessment.possible_conditions[0].confidence == 0.9

    def test_default_values(self):
        """Should use defaults for optional fields."""
        assessment = StructuredAssessment(chief_complaint="Headache")
        assert assessment.severity == Severity.MODERATE
        assert assessment.triage_level == TriageLevel.YELLOW
        assert assessment.symptoms == []
        assert assessment.possible_conditions == []

    def test_invalid_severity_rejected(self):
        """Should reject invalid severity values."""
        with pytest.raises(ValueError):
            StructuredAssessment(
                chief_complaint="Test",
                severity="INVALID",
            )

    def test_confidence_bounds(self):
        """Should reject confidence values outside 0-1."""
        with pytest.raises(ValueError):
            StructuredAssessment(
                chief_complaint="Test",
                possible_conditions=[
                    {"name": "Test", "icd10": "Z00", "confidence": 1.5}
                ],
            )
