from enum import Enum


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def get_risk_level(risk_score: float) -> RiskLevel:
    """
    Convert a risk score (0-100) into a risk level.
    """

    if risk_score < 15:
        return RiskLevel.LOW

    elif risk_score < 20:
        return RiskLevel.MEDIUM

    elif risk_score < 25:
        return RiskLevel.HIGH

    else:
        return RiskLevel.CRITICAL