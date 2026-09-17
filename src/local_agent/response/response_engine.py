from enum import Enum
from typing import Dict, Any


class ResponseAction(Enum):
    """
    Security action to take based on the current risk level.
    """

    CONTINUE = "CONTINUE"
    INCREASE_MONITORING = "INCREASE_MONITORING"
    RESTRICT = "RESTRICT"
    BEHAVIORAL_LOCK = "BEHAVIORAL_LOCK"


class ResponseEngine:
    """
    Converts Risk Engine output into a security response.

    Risk calculation is handled by RiskEngine.
    This class only decides what response should be triggered.
    """

    def determine_action(
        self,
        risk_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Determine the appropriate security response.
        """

        self._validate_input(risk_result)

        risk_level = risk_result["risk_level"]
        profile_update_allowed = bool(
            risk_result["profile_update_allowed"]
        )

        # --------------------------------------------------
        # LOW
        # --------------------------------------------------

        if risk_level == "LOW":
            action = ResponseAction.CONTINUE
            lock_required = False
            monitoring_level = "NORMAL"

        # --------------------------------------------------
        # MEDIUM
        # --------------------------------------------------

        elif risk_level == "MEDIUM":
            action = ResponseAction.INCREASE_MONITORING
            lock_required = False
            monitoring_level = "ELEVATED"

        # --------------------------------------------------
        # HIGH
        # --------------------------------------------------

        elif risk_level == "HIGH":
            action = ResponseAction.RESTRICT
            lock_required = False
            monitoring_level = "HIGH"

        # --------------------------------------------------
        # CRITICAL
        # --------------------------------------------------

        elif risk_level == "CRITICAL":
            action = ResponseAction.BEHAVIORAL_LOCK
            lock_required = True
            monitoring_level = "CRITICAL"

        else:
            raise ValueError(
                f"Unknown risk level: {risk_level}"
            )

        # Suspicious/high-risk behaviour must never
        # update the legitimate behavioural profile.
        if risk_level in ("HIGH", "CRITICAL"):
            profile_update_allowed = False

        return {
            "risk_score": risk_result["risk_score"],
            "risk_level": risk_level,
            "action": action.value,
            "lock_required": lock_required,
            "monitoring_level": monitoring_level,
            "profile_update_allowed": profile_update_allowed,
        }

    @staticmethod
    def _validate_input(
        risk_result: Dict[str, Any],
    ) -> None:
        """
        Validate the minimum Risk Engine output required
        by the Response Engine.
        """

        required_fields = [
            "risk_score",
            "risk_level",
            "profile_update_allowed",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in risk_result
        ]

        if missing_fields:
            raise ValueError(
                f"Missing risk result fields: {missing_fields}"
            )