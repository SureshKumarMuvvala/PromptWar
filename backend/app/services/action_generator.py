"""
Action generator — maps validated triage assessments
to concrete real-world emergency actions.
"""

from typing import Optional

from app.models.enums import Severity, ActionType
from app.models.schemas import (
    StructuredAssessment,
    RAGValidation,
    RecommendedAction,
    HospitalInfo,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ActionGenerator:
    """
    Rule-based engine that generates prioritized emergency actions
    based on clinical severity and RAG validations.
    """

    def generate(
        self,
        assessment: StructuredAssessment,
        validation: Optional[RAGValidation] = None,
        location: Optional[dict] = None,
        hospitals: Optional[list[HospitalInfo]] = None,
    ) -> list[RecommendedAction]:
        """
        Generate a prioritized list of recommended actions.

        Args:
            assessment: The structured clinical assessment.
            validation: Optional validation results from RAG.
            location: Optional user coordinates for hospital search.
            hospitals: Optional list of actual nearby hospitals.

        Returns:
            A list of RecommendedAction objects ordered by priority.
        """
        # Apply any RAG corrections to severity
        effective_severity = assessment.severity
        if validation and validation.corrections:
            for correction in validation.corrections:
                if correction.field == "severity":
                    effective_severity = Severity(correction.corrected)
                    logger.info(
                        f"Severity corrected by RAG: "
                        f"{assessment.severity} → {effective_severity}"
                    )

        actions: list[RecommendedAction] = []

        # ── CRITICAL ─────────────────────────────────────────────
        if effective_severity == Severity.CRITICAL:
            actions.append(
                RecommendedAction(
                    type=ActionType.CALL_AMBULANCE,
                    priority=1,
                    description=(
                        "Call 112/911 immediately — "
                        f"suspected {assessment.chief_complaint.lower()}. "
                        "This is a life-threatening emergency."
                    ),
                    auto_triggered=True,
                )
            )
            actions.append(
                RecommendedAction(
                    type=ActionType.FIRST_AID,
                    priority=2,
                    description=self._get_first_aid(assessment),
                )
            )
            actions.append(
                RecommendedAction(
                    type=ActionType.EMERGENCY_CONTACT_ALERT,
                    priority=3,
                    description="Alert emergency contacts about the situation.",
                    auto_triggered=True,
                )
            )

        # ── HIGH ──────────────────────────────────────────────────
        elif effective_severity == Severity.HIGH:
            actions.append(
                RecommendedAction(
                    type=ActionType.FIRST_AID,
                    priority=1,
                    description=self._get_first_aid(assessment),
                )
            )
            actions.append(
                RecommendedAction(
                    type=ActionType.CALL_AMBULANCE,
                    priority=2,
                    description=(
                        "Consider calling an ambulance or go to the nearest ER. "
                        f"Condition: {assessment.chief_complaint}."
                    ),
                    auto_triggered=False,
                )
            )

        # ── MODERATE ──────────────────────────────────────────────
        elif effective_severity == Severity.MODERATE:
            actions.append(
                RecommendedAction(
                    type=ActionType.FIRST_AID,
                    priority=1,
                    description=self._get_first_aid(assessment),
                )
            )
            actions.append(
                RecommendedAction(
                    type=ActionType.FOLLOW_UP,
                    priority=2,
                    description=(
                        "Visit a clinic or urgent care within the next few hours. "
                        "Monitor symptoms and seek emergency care if they worsen."
                    ),
                )
            )

        # ── LOW ───────────────────────────────────────────────────
        else:
            actions.append(
                RecommendedAction(
                    type=ActionType.SELF_CARE,
                    priority=1,
                    description=self._get_self_care(assessment),
                )
            )
            actions.append(
                RecommendedAction(
                    type=ActionType.FOLLOW_UP,
                    priority=2,
                    description=(
                        "Schedule a visit with your primary care physician "
                        "if symptoms persist for more than 48 hours."
                    ),
                )
            )

        # ── Hospital suggestion (all severity levels except LOW) ──
        if effective_severity != Severity.LOW:
            hospital_action = RecommendedAction(
                type=ActionType.HOSPITAL_SUGGESTION,
                priority=len(actions) + 1,
                description="Nearest hospitals with emergency departments:",
                hospitals=hospitals or [],
            )
            actions.append(hospital_action)

        return actions

    def _get_first_aid(self, assessment: StructuredAssessment) -> str:
        """Generate first-aid instructions based on the chief complaint."""
        complaint = assessment.chief_complaint.lower()

        if any(kw in complaint for kw in ["chest pain", "heart", "cardiac"]):
            return (
                "Have the patient sit upright in a comfortable position. "
                "If not allergic, chew 325mg aspirin. Loosen tight clothing. "
                "Do NOT let the patient exert themselves. Be ready to perform CPR."
            )
        elif any(kw in complaint for kw in ["burn", "scald"]):
            return (
                "Cool the burn under cool running water for at least 20 minutes. "
                "Remove jewelry/clothing near the burn (if not stuck). "
                "Cover with a clean, non-fluffy dressing. Do NOT apply butter or ice."
            )
        elif any(kw in complaint for kw in ["fracture", "broken", "bone"]):
            return (
                "Immobilize the affected area — do not attempt to realign. "
                "Apply a splint if available. Apply ice wrapped in cloth. "
                "Elevate the injury if possible."
            )
        elif any(kw in complaint for kw in ["bleed", "hemorrhage", "cut", "laceration"]):
            return (
                "Apply direct pressure with a clean cloth. "
                "Elevate the wound above heart level if possible. "
                "Do NOT remove the cloth if blood soaks through — add more layers."
            )
        elif any(kw in complaint for kw in ["choking", "airway"]):
            return (
                "Perform the Heimlich maneuver (abdominal thrusts). "
                "If the patient becomes unconscious, begin CPR. "
                "Call emergency services immediately."
            )
        elif any(kw in complaint for kw in ["allergic", "anaphylaxis", "allergy"]):
            return (
                "Use an epinephrine auto-injector if available. "
                "Have the patient lie flat with legs elevated. "
                "Call emergency services immediately."
            )
        elif any(kw in complaint for kw in ["stroke", "speech", "face droop"]):
            return (
                "Note the time symptoms started — this is critical for treatment. "
                "Keep the patient still and comfortable. "
                "Do NOT give food, drink, or medication."
            )
        else:
            return (
                f"Keep the patient calm and comfortable. "
                f"Monitor symptoms closely — {assessment.chief_complaint}. "
                f"Do not give medication without medical advice."
            )

    def _get_self_care(self, assessment: StructuredAssessment) -> str:
        """Generate self-care advice for low-severity conditions."""
        return (
            f"For {assessment.chief_complaint.lower()}: "
            "Rest, stay hydrated, and monitor symptoms. "
            "Take over-the-counter pain relief if needed (follow dosage instructions). "
            "Seek medical attention if symptoms worsen or new symptoms develop."
        )
