from typing import Dict, Any

from .risk_levels import RiskLevel, get_risk_level
from .temporal import TemporalAnalyzer
from .thresholds import (
    ANOMALY_WEIGHT,
    RECENT_ANOMALY_WEIGHT,
    CONFIDENCE_WEIGHT,
    PERSISTENCE_WEIGHT,
    MAX_CONSECUTIVE_DEVIATIONS,
)


class RiskEngine:
    """
    Converts behavioural ML output into a risk score and risk level.

    Input:
        Output from Member 3's behavioural authentication module.

    Output:
        Risk score, risk level and supporting information.
    """

    def __init__(self):
        self.temporal_analyzer = TemporalAnalyzer()

    def calculate_risk(self, ml_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate the current session risk from Member 3's output.
        """

        self._validate_input(ml_output)

        anomaly_score = self._clamp(
            ml_output["anomaly_score"]
        )

        legitimate_confidence = self._clamp(
            ml_output["legitimate_confidence"]
        )

        consecutive_deviation_count = max(
            0,
            int(ml_output["consecutive_deviation_count"])
        )

        has_repeated_deviation = bool(
            ml_output["has_repeated_deviation"]
        )

        model_state = ml_output["model_state"]

        # --------------------------------------------------
        # 1. Update temporal history
        # --------------------------------------------------

        # Member 3 owns its deviation-history calculation and supplies the
        # result as part of the cross-team contract. Keep a local history for
        # diagnostics, but do not silently replace that value.
        self.temporal_analyzer.update(anomaly_score)
        recent_anomaly_average = self._clamp(
            ml_output["recent_anomaly_average"]
        )

        # --------------------------------------------------
        # 2. Calculate individual risk components
        # --------------------------------------------------

        current_anomaly_risk = anomaly_score

        recent_anomaly_risk = recent_anomaly_average

        # Low legitimate confidence means higher risk.
        confidence_risk = 1.0 - legitimate_confidence

        # Convert persistence into a value between 0 and 1.
        persistence_risk = min(
            consecutive_deviation_count
            / MAX_CONSECUTIVE_DEVIATIONS,
            1.0
        )

        # Repeated deviation provides additional persistence evidence.
        if has_repeated_deviation:
            persistence_risk = max(
                persistence_risk,
                0.5
            )

        # --------------------------------------------------
        # 3. Weighted risk calculation
        # --------------------------------------------------

        normalized_risk = (
            current_anomaly_risk * ANOMALY_WEIGHT
            + recent_anomaly_risk * RECENT_ANOMALY_WEIGHT
            + confidence_risk * CONFIDENCE_WEIGHT
            + persistence_risk * PERSISTENCE_WEIGHT
        )

        risk_score = round(
            normalized_risk * 100,
            2
        )

        # --------------------------------------------------
        # 4. Determine risk level
        # --------------------------------------------------

        risk_level = get_risk_level(risk_score)

        # --------------------------------------------------
        # 5. Security-related profile update decision
        # --------------------------------------------------

        profile_update_allowed = bool(
            ml_output["profile_update_allowed"]
        )

        # Never allow this module to override Member 3's
        # decision and enable profile learning.
        if risk_level in (
            RiskLevel.HIGH,
            RiskLevel.CRITICAL
        ):
            profile_update_allowed = False

        # --------------------------------------------------
        # 6. Return result
        # --------------------------------------------------

        return {
            "risk_score": risk_score,
            "risk_level": risk_level.value,

            "current_anomaly_risk": round(
                current_anomaly_risk * 100,
                2
            ),

            "recent_anomaly_risk": round(
                recent_anomaly_risk * 100,
                2
            ),

            "confidence_risk": round(
                confidence_risk * 100,
                2
            ),

            "persistence_risk": round(
                persistence_risk * 100,
                2
            ),

            "model_state": model_state,

            "is_deviation": ml_output["is_deviation"],

            "consecutive_deviation_count":
                consecutive_deviation_count,

            "has_repeated_deviation":
                has_repeated_deviation,

            "profile_update_allowed":
                profile_update_allowed,
        }

    @staticmethod
    def _validate_input(ml_output: Dict[str, Any]) -> None:
        """
        Validate the required output from Member 3.
        """

        required_fields = [
            "anomaly_score",
            "legitimate_confidence",
            "is_deviation",
            "recent_anomaly_average",
            "consecutive_deviation_count",
            "has_repeated_deviation",
            "model_state",
            "profile_update_allowed",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in ml_output
        ]

        if missing_fields:
            raise ValueError(
                f"Missing ML output fields: {missing_fields}"
            )

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))
