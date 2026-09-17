from src.ml.behavior_authenticator import BehaviorAuthenticator
from src.ml.feature_contract import validate_feature_vector
from src.ml.model_manager import (
    load_model_bundle,
    save_model_bundle,
)
from src.ml.profile_builder import ProfileBuilder
from src.ml.train_model import train_isolation_forest


MODE_ENROLMENT = "ENROLMENT"
MODE_ACTIVE = "ACTIVE"


class AuthenticationPipeline:
    """
    Manage enrolment and active behavioural authentication.
    """

    def __init__(
        self,
        model_path=None,
        profile_builder=None,
        authenticator=None,
    ):

        self.model_path = model_path
        self.profile_builder = (
            profile_builder
            if profile_builder is not None
            else ProfileBuilder()
        )
        self.authenticator = authenticator
        self.mode = MODE_ENROLMENT

        if self.authenticator is not None:
            self.mode = MODE_ACTIVE
            return

        try:
            model_bundle = load_model_bundle(model_path)
        except FileNotFoundError:
            return

        self.authenticator = BehaviorAuthenticator(
            model_bundle=model_bundle
        )
        self.mode = MODE_ACTIVE

    def process_feature_vector(self, feature_vector):
        """
        Process one Member 2 feature vector.
        """

        validated_vector = validate_feature_vector(
            feature_vector
        )

        if self.mode == MODE_ACTIVE:
            return self.authenticator.analyze_for_risk_engine(
                validated_vector
            )

        self.profile_builder.add_sample(validated_vector)

        if not self.profile_builder.is_ready():
            return self._build_enrolment_result(
                model_trained=False,
                model_path=None,
            )

        model_bundle = train_isolation_forest(
            self.profile_builder.get_samples()
        )

        saved_model_path = save_model_bundle(
            model_bundle,
            self.model_path,
        )

        self.authenticator = BehaviorAuthenticator(
            model_bundle=model_bundle
        )
        self.mode = MODE_ACTIVE

        return self._build_enrolment_result(
            model_trained=True,
            model_path=saved_model_path,
            mode=MODE_ACTIVE,
        )

    def get_mode(self):
        """
        Return current pipeline mode.
        """

        return self.mode

    def _build_enrolment_result(
        self,
        model_trained,
        model_path,
        mode=MODE_ENROLMENT,
    ):

        return {
            "mode": mode,
            "sample_count": self.profile_builder.sample_count(),
            "is_ready": self.profile_builder.is_ready(),
            "model_trained": model_trained,
            "model_path": model_path,
        }
