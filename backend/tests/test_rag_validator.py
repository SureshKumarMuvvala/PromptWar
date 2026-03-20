"""
Tests for the RAG validator.
"""

import pytest
from app.models.schemas import StructuredAssessment, RAGCorrection
from app.models.enums import Severity
from app.services.rag_validator import RAGValidator


class TestCrossCheck:
    """Tests for the RAG severity cross-check logic."""

    def test_no_correction_when_severity_matches(self):
        """Should not correct when severity matches protocol."""
        validator = RAGValidator.__new__(RAGValidator)
        assessment = StructuredAssessment(
            chief_complaint="Chest pain",
            symptoms=["chest_pain"],
            severity=Severity.CRITICAL,
        )
        matched_docs = [
            {"protocol_id": "ACS_001", "expected_severity": "CRITICAL"}
        ]
        corrections = validator._cross_check(assessment, matched_docs)
        assert len(corrections) == 0

    def test_correction_when_severity_too_low(self):
        """Should correct when severity is understated."""
        validator = RAGValidator.__new__(RAGValidator)
        assessment = StructuredAssessment(
            chief_complaint="Chest pain",
            symptoms=["chest_pain"],
            severity=Severity.MODERATE,
        )
        matched_docs = [
            {
                "protocol_id": "ACS_001",
                "expected_severity": "CRITICAL",
                "correction_reason": "ACS requires CRITICAL severity.",
            }
        ]
        corrections = validator._cross_check(assessment, matched_docs)
        assert len(corrections) == 1
        assert corrections[0].field == "severity"
        assert corrections[0].corrected == "CRITICAL"

    def test_no_correction_when_severity_higher(self):
        """Should not correct when current severity is higher than protocol."""
        validator = RAGValidator.__new__(RAGValidator)
        assessment = StructuredAssessment(
            chief_complaint="Minor cut",
            symptoms=["minor_cut"],
            severity=Severity.HIGH,
        )
        matched_docs = [
            {"protocol_id": "WOUND_010", "expected_severity": "LOW"}
        ]
        corrections = validator._cross_check(assessment, matched_docs)
        assert len(corrections) == 0
