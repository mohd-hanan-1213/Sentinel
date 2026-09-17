"""Runtime boundary joining Member 2, Member 3, and Member 4."""

from datetime import datetime

from src.local_agent.response.behavioral_lock import BehavioralLock
from src.local_agent.response.response_engine import ResponseEngine
from src.local_agent.risk.risk_engine import RiskEngine


FEATURE_ORDER = (
    "keyboard.average_hold_time",
    "keyboard.average_flight_time",
    "keyboard.typing_speed",
    "keyboard.average_pause_duration",
    "keyboard.correction_rate",
    "mouse.average_speed",
    "mouse.average_distance",
    "mouse.average_click_duration",
    "mouse.average_acceleration",
    "mouse.direction_changes",
    "mouse.click_rate",
    "mouse.idle_ratio",
)


class SentinelPipeline:
    """
    Process one behavioural feature window through:

        Features -> ML -> Risk -> Response -> Behavioral Lock

    Database persistence is optional and injected separately.
    """

    def __init__(
        self,
        analyzer=None,
        risk_engine=None,
        response_engine=None,
        behavioral_lock=None,
        session_factory=None,
    ):
        self.analyzer = analyzer or self._load_member3_analyzer()
        self.risk_engine = risk_engine or RiskEngine()
        self.response_engine = response_engine or ResponseEngine()
        self.behavioral_lock = behavioral_lock or BehavioralLock()
        self.session_factory = session_factory

    @staticmethod
    def _load_member3_analyzer():
        try:
            from src.ml.behavior_authenticator import BehaviorAuthenticator
        except ImportError as error:
            raise RuntimeError(
                "Member 3 ML module is not available."
            ) from error

        return BehaviorAuthenticator()

    @staticmethod
    def flatten_features(features):
        """
        Validate and return the 12-value Member 3 feature vector.
        """

        if not isinstance(features, (list, tuple)):
            raise ValueError("Feature window must be a list or tuple.")

        if len(features) != len(FEATURE_ORDER):
            raise ValueError(
                f"Feature window must contain {len(FEATURE_ORDER)} values."
            )

        try:
            return [float(value) for value in features]
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Feature window contains an invalid value."
            ) from error

    def start_session(self, user_id):
        """
        Create a database session.

        The database session factory must be provided for persistence.
        """

        if self.session_factory is None:
            raise RuntimeError(
                "Database session factory is not configured."
            )

        from src.local_agent.database.models import Session

        with self.session_factory() as db:
            session = Session(
                user_id=user_id,
                status="ACTIVE",
            )
            db.add(session)
            db.commit()
            return session.id

    def process_features(self, session_id, features):
        """
        Process one feature window.

        If a database session factory is configured, the security
        result is persisted. Otherwise the ML/Risk/Response chain
        still executes normally.
        """

        vector = self.flatten_features(features)

        # --------------------------------------------------
        # Member 3: Behavioural ML
        # --------------------------------------------------

        ml_output = self.analyzer.analyze_for_risk_engine(vector)

        # --------------------------------------------------
        # Member 4: Risk Engine
        # --------------------------------------------------

        risk_result = self.risk_engine.calculate_risk(ml_output)

        # --------------------------------------------------
        # Member 4: Response Engine
        # --------------------------------------------------

        response = self.response_engine.determine_action(risk_result)

        captured_at = datetime.utcnow()

        # --------------------------------------------------
        # Optional database persistence
        # --------------------------------------------------

        if self.session_factory is not None:
            self._persist_result(
                session_id=session_id,
                ml_output=ml_output,
                risk_result=risk_result,
                response=response,
                timestamp=captured_at,
            )

        # --------------------------------------------------
        # Behavioral Lock
        # --------------------------------------------------

        if response["lock_required"]:
            self.behavioral_lock.lock()

            # CRITICAL risk activates the Windows workstation lock.
            response["windows_locked"] = (
                self.behavioral_lock.lock_windows_session()
            )
        else:
            response["windows_locked"] = False

        return {
            "ml_output": ml_output,
            "risk": risk_result,
            "response": response,
        }

    def _persist_result(
        self,
        session_id,
        ml_output,
        risk_result,
        response,
        timestamp,
    ):
        from src.local_agent.database.models import (
            RiskEvent,
            SecurityEvent,
        )

        with self.session_factory() as db:
            risk_event = RiskEvent(
                session_id=session_id,
                timestamp=timestamp,
                anomaly_score=ml_output["anomaly_score"],
                confidence_score=ml_output["legitimate_confidence"],
                risk_score=risk_result["risk_score"],
                risk_level=risk_result["risk_level"],
                event_type="BEHAVIORAL_ANALYSIS",
                response=response["action"],
            )

            db.add(risk_event)
            db.flush()

            db.add(
                SecurityEvent(
                    session_id=session_id,
                    timestamp=timestamp,
                    event_type=response["action"],
                    severity=response["risk_level"],
                    description=(
                        f"Behavioural response: {response['action']}"
                    ),
                    status=(
                        "OPEN"
                        if response["risk_level"] != "LOW"
                        else "RESOLVED"
                    ),
                )
            )

            db.commit()