STATE_ENROLMENT = "ENROLMENT"
STATE_LEARNING = "LEARNING"
STATE_ACTIVE = "ACTIVE"
STATE_SUSPICIOUS = "SUSPICIOUS"
STATE_FROZEN = "FROZEN"


DEFAULT_TRUSTED_CONFIDENCE_THRESHOLD = 0.70
DEFAULT_SUSPICIOUS_ANOMALY_THRESHOLD = 0.60
DEFAULT_FREEZE_CONSECUTIVE_DEVIATIONS = 3


class LearningGate:
    """
    Decide whether new behaviour is trusted enough to update
    the legitimate-user profile.
    """

    def __init__(
        self,
        initial_state=STATE_ACTIVE,
        trusted_confidence_threshold=(
            DEFAULT_TRUSTED_CONFIDENCE_THRESHOLD
        ),
        suspicious_anomaly_threshold=(
            DEFAULT_SUSPICIOUS_ANOMALY_THRESHOLD
        ),
        freeze_consecutive_deviations=(
            DEFAULT_FREEZE_CONSECUTIVE_DEVIATIONS
        ),
    ):

        self._validate_state(initial_state)

        if not 0.0 <= trusted_confidence_threshold <= 1.0:
            raise ValueError(
                "Trusted confidence threshold must be between "
                "0.0 and 1.0."
            )

        if not 0.0 <= suspicious_anomaly_threshold <= 1.0:
            raise ValueError(
                "Suspicious anomaly threshold must be between "
                "0.0 and 1.0."
            )

        if freeze_consecutive_deviations <= 0:
            raise ValueError(
                "Freeze consecutive deviations must be positive."
            )

        self.state = initial_state
        self.trusted_confidence_threshold = (
            trusted_confidence_threshold
        )
        self.suspicious_anomaly_threshold = (
            suspicious_anomaly_threshold
        )
        self.freeze_consecutive_deviations = (
            freeze_consecutive_deviations
        )

    def evaluate(
        self,
        anomaly_result,
        history_summary=None,
    ):
        """
        Return whether profile/model updating is allowed.
        """

        anomaly_result = self._validate_anomaly_result(
            anomaly_result
        )

        history_summary = self._validate_history_summary(
            history_summary
        )

        if self._should_freeze(history_summary):
            self.state = STATE_FROZEN

            return self._decision(
                profile_update_allowed=False,
                reason="repeated deviation detected",
            )

        if self._is_trusted(anomaly_result, history_summary):
            self.state = STATE_ACTIVE

            return self._decision(
                profile_update_allowed=True,
                reason="trusted behaviour",
            )

        self.state = STATE_SUSPICIOUS

        return self._decision(
            profile_update_allowed=False,
            reason="low confidence or suspicious behaviour",
        )

    def get_state(self):
        """
        Return the current learning gate state.
        """

        return self.state

    def reset_to_active(self):
        """
        Reset state after successful re-authentication.
        """

        self.state = STATE_ACTIVE

        return self.state

    def _is_trusted(
        self,
        anomaly_result,
        history_summary,
    ):

        if history_summary.get("has_repeated_deviation", False):
            return False

        return (
            anomaly_result["legitimate_confidence"]
            >= self.trusted_confidence_threshold
            and anomaly_result["anomaly_score"]
            < self.suspicious_anomaly_threshold
            and not anomaly_result["is_deviation"]
        )

    def _should_freeze(self, history_summary):

        return (
            history_summary.get("has_repeated_deviation", False)
            or history_summary.get(
                "consecutive_deviation_count",
                0,
            )
            >= self.freeze_consecutive_deviations
        )

    def _decision(
        self,
        profile_update_allowed,
        reason,
    ):

        return {
            "profile_update_allowed": profile_update_allowed,
            "model_state": self.state,
            "reason": reason,
        }

    @staticmethod
    def _validate_state(state):

        valid_states = {
            STATE_ENROLMENT,
            STATE_LEARNING,
            STATE_ACTIVE,
            STATE_SUSPICIOUS,
            STATE_FROZEN,
        }

        if state not in valid_states:
            raise ValueError(
                f"Invalid learning gate state: {state}"
            )

    @staticmethod
    def _validate_anomaly_result(anomaly_result):

        if not isinstance(anomaly_result, dict):
            raise ValueError(
                "Anomaly result must be a dictionary."
            )

        required_keys = [
            "anomaly_score",
            "legitimate_confidence",
            "is_deviation",
        ]

        missing_keys = [
            key
            for key in required_keys
            if key not in anomaly_result
        ]

        if missing_keys:
            raise ValueError(
                "Anomaly result is missing required keys: "
                + ", ".join(missing_keys)
            )

        anomaly_score = anomaly_result["anomaly_score"]
        legitimate_confidence = (
            anomaly_result["legitimate_confidence"]
        )

        if not 0.0 <= anomaly_score <= 1.0:
            raise ValueError(
                "Anomaly score must be between 0.0 and 1.0."
            )

        if not 0.0 <= legitimate_confidence <= 1.0:
            raise ValueError(
                "Legitimate confidence must be between 0.0 and 1.0."
            )

        if not isinstance(anomaly_result["is_deviation"], bool):
            raise ValueError(
                "is_deviation must be a boolean."
            )

        return dict(anomaly_result)

    @staticmethod
    def _validate_history_summary(history_summary):

        if history_summary is None:
            return {}

        if not isinstance(history_summary, dict):
            raise ValueError(
                "History summary must be a dictionary."
            )

        return dict(history_summary)
