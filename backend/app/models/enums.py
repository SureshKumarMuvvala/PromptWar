"""
Enumerations used across the application.
"""

from enum import Enum


class Severity(str, Enum):
    """Emergency severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class TriageLevel(str, Enum):
    """Standard triage color codes."""
    RED = "RED"          # Immediate — life-threatening
    ORANGE = "ORANGE"    # Very urgent
    YELLOW = "YELLOW"    # Urgent
    GREEN = "GREEN"      # Standard
    BLUE = "BLUE"        # Non-urgent


class InputType(str, Enum):
    """Types of multimodal input."""
    TEXT = "TEXT"
    AUDIO = "AUDIO"
    IMAGE = "IMAGE"


class ActionType(str, Enum):
    """Types of recommended emergency actions."""
    CALL_AMBULANCE = "CALL_AMBULANCE"
    HOSPITAL_SUGGESTION = "HOSPITAL_SUGGESTION"
    FIRST_AID = "FIRST_AID"
    SELF_CARE = "SELF_CARE"
    EMERGENCY_CONTACT_ALERT = "EMERGENCY_CONTACT_ALERT"
    FOLLOW_UP = "FOLLOW_UP"
