from src.ml.anomaly_detector import detect_anomaly
from src.ml.deviation_history import DeviationHistory
from src.ml.learning_gate import LearningGate
from src.ml.model_manager import (
    load_model_bundle,
    validate_model_bundle,
)


class BehaviorAuthenticator:
    """
    Integrate anomaly detection, deviation history, and learning gate.
    """

    def __init__(
        self,
        model_bundle=None,
        model_path=None,
        deviation_history=None,
        learning_gate=None,
    ):

        if model_bundle is None:
            model_bundle = load_model_bundle(model_path)
        else:
            validate_model_bundle(model_bundle)

        self.model_bundle = model_bundle
        self.deviation_history = (
            deviation_history
            if deviation_history is not None
            else DeviationHistory()
        )
        self.learning_gate = (
            learning_gate
            if learning_gate is not None
            else LearningGate()
        )

    def analyze(self, feature_vector):
        """
        Analyze one behavioural feature vector for Member 4.
        """

        anomaly_result = detect_anomaly(
            feature_vector,
            model_bundle=self.model_bundle,
        )

        self.deviation_history.add_result(anomaly_result)
        history_summary = self.deviation_history.build_summary()

        gate_result = self.learning_gate.evaluate(
            anomaly_result,
            history_summary,
        )

        return {
            **anomaly_result,
            "recent_anomaly_average": (
                history_summary["recent_anomaly_average"]
            ),
            "consecutive_deviation_count": (
                history_summary["consecutive_deviation_count"]
            ),
            "has_repeated_deviation": (
                history_summary["has_repeated_deviation"]
            ),
            "history_window_count": history_summary["window_count"],
            "profile_update_allowed": (
                gate_result["profile_update_allowed"]
            ),
            "model_state": gate_result["model_state"],
            "learning_gate_reason": gate_result["reason"],
        }

    def get_history_summary(self):
        """
        Return the current deviation history summary.
        """

        return self.deviation_history.build_summary()

    def analyze_for_risk_engine(self, feature_vector):
        """
        Return the clean Member 4 risk-engine result.
        """

        result = self.analyze(feature_vector)

        return {
            "anomaly_score": result["anomaly_score"],
            "legitimate_confidence": (
                result["legitimate_confidence"]
            ),
            "is_deviation": result["is_deviation"],
            "recent_anomaly_average": (
                result["recent_anomaly_average"]
            ),
            "consecutive_deviation_count": (
                result["consecutive_deviation_count"]
            ),
            "has_repeated_deviation": (
                result["has_repeated_deviation"]
            ),
            "profile_update_allowed": (
                result["profile_update_allowed"]
            ),
            "model_state": result["model_state"],
        }

    def reset_learning_gate(self):
        """
        Reset the learning gate after successful re-authentication.
        """

        return self.learning_gate.reset_to_active()
