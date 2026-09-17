from src.ml.behavior_authenticator import BehaviorAuthenticator
from src.local_agent.risk.risk_engine import RiskEngine


class MLRiskPipeline:
    """
    Connect Member 3's behavioural ML system
    to Member 4's Risk Engine.
    """

    def __init__(
        self,
        model_bundle=None,
        model_path=None,
    ):
        self.behavior_authenticator = BehaviorAuthenticator(
            model_bundle=model_bundle,
            model_path=model_path,
        )

        self.risk_engine = RiskEngine()

    def analyze(self, feature_vector):
        """
        Send one 12-feature vector through ML
        and then through the Risk Engine.
        """

        ml_output = (
            self.behavior_authenticator
            .analyze_for_risk_engine(feature_vector)
        )

        risk_result = self.risk_engine.calculate_risk(
            ml_output
        )

        return {
            "ml_output": ml_output,
            "risk_result": risk_result,
        }

    def get_history_summary(self):
        """
        Return the recent ML deviation history.
        """

        return (
            self.behavior_authenticator
            .get_history_summary()
        )

    def reset_learning_gate(self):
        """
        Reset the learning gate after
        successful re-authentication.
        """

        return (
            self.behavior_authenticator
            .reset_learning_gate()
        )