"""
RAG-based clinical validator using FAISS for protocol retrieval.
"""

import os
import json
from typing import Optional

import numpy as np

from app.config import get_settings
from app.models.schemas import StructuredAssessment, RAGValidation, RAGCorrection
from app.services.gemini_client import GeminiClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Lazy import — FAISS may not be installed in all environments
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not installed. RAG validation will run in degraded mode.")


class RAGValidator:
    """
    Validates structured assessments against a clinical knowledge base (RAG).
    Ensures that the LLM's triage and severity align with standard medical protocols.
    """

    def __init__(self, gemini_client: GeminiClient):
        """
        Initializes the RAG validator.

        Args:
            gemini_client: An initialized GeminiClient instance for embeddings and analysis.
        """
        self.gemini = gemini_client
        self.settings = get_settings()
        self.index: Optional[object] = None
        self.documents: list[dict] = []
        self.index_loaded = False

    def load_index(self) -> bool:
        """
        Load the FAISS index and associated document metadata from disk.

        Returns:
            True if the index was loaded successfully, False otherwise.
        """
        if not FAISS_AVAILABLE:
            logger.warning("FAISS not available — skipping index load")
            return False

        index_path = os.path.join(self.settings.FAISS_INDEX_PATH, "index.faiss")
        docs_path = os.path.join(self.settings.FAISS_INDEX_PATH, "documents.json")

        if not os.path.exists(index_path) or not os.path.exists(docs_path):
            logger.warning(f"FAISS index not found at {index_path}")
            return False

        try:
            self.index = faiss.read_index(index_path)
            with open(docs_path, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            self.index_loaded = True
            logger.info(
                f"FAISS index loaded: {self.index.ntotal} vectors, "
                f"{len(self.documents)} documents"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            return False

    async def validate(self, assessment: StructuredAssessment) -> RAGValidation:
        """
        Validate the provided assessment against indexed medical protocols.

        Args:
            assessment: The structured assessment to validate.

        Returns:
            A RAGValidation object containing matched protocols and corrections.
        """
        if not self.index_loaded:
            logger.warning("FAISS index not loaded, skipping clinical validation")
            return RAGValidation(validated=True, confidence_score=0.5)

        logger.info(f"Validating assessment: {assessment.chief_complaint}")

        # Build query from assessment
        query_text = (
            f"Emergency: {assessment.chief_complaint}. "
            f"Symptoms: {', '.join(assessment.symptoms)}. "
            f"Severity: {assessment.severity.value}."
        )

        # Embed and search
        query_vector = await self.gemini.get_embeddings(query_text)
        query_np = np.array([query_vector], dtype=np.float32)

        distances, indices = self.index.search(query_np, self.settings.RAG_TOP_K)

        # Collect matched protocols
        matched_protocols = []
        matched_docs = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            doc = self.documents[idx]
            matched_protocols.append(doc.get("protocol_id", f"DOC_{idx}"))
            matched_docs.append(doc)

        # Calculate confidence from distances (L2 similarity)
        if len(distances[0]) > 0 and distances[0][0] >= 0:
            max_distance = float(distances[0][-1]) if distances[0][-1] > 0 else 1.0
            confidence = max(0, 1 - (float(distances[0][0]) / (max_distance + 1)))
        else:
            confidence = 0.0

        # Cross-check severity against matched protocols
        corrections = self._cross_check(assessment, matched_docs)

        return RAGValidation(
            validated=len(corrections) == 0,
            matched_protocols=matched_protocols,
            confidence_score=round(confidence, 3),
            corrections=corrections,
        )

    def _cross_check(
        self, assessment: StructuredAssessment, matched_docs: list[dict]
    ) -> list[RAGCorrection]:
        """
        Compare the assessment against matched protocol documents
        and suggest corrections if there are mismatches.
        """
        corrections = []
        for doc in matched_docs:
            expected_severity = doc.get("severity")
            if (
                expected_severity
                and expected_severity != assessment.severity.value
            ):
                severity_order = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
                current_idx = severity_order.index(assessment.severity.value)
                expected_idx = severity_order.index(expected_severity)
                # Only correct if protocol says severity should be HIGHER
                if expected_idx > current_idx:
                    corrections.append(
                        RAGCorrection(
                            field="severity",
                            original=assessment.severity.value,
                            corrected=expected_severity,
                            reason=doc.get(
                                "correction_reason",
                                f"Protocol {doc.get('protocol_id', 'UNKNOWN')} "
                                f"indicates {expected_severity} severity for this condition.",
                            ),
                        )
                    )
                    break
        return corrections
