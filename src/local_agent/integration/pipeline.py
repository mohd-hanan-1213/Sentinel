"""Runtime boundary joining Member 2, Member 3, and Member 4."""

from datetime import datetime

from src.local_agent.camera.evidence import CameraEvidenceService
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

        Features -> ML -> Risk -> Response
        -> Camera Evidence -> Behavioral Lock
        -> Windows Lock
    """

    def __init__(
        self,
        analyzer=None,
        risk_engine=None,
        response_engine=None,
        behavioral_lock=None,
        camera_service=None,
        session_factory=None,
    ):
        self.analyzer = analyzer or self._load_member3_analyzer()
        self.risk_engine = risk_engine or RiskEngine()
        self.response_engine = response_engine or ResponseEngine()
        self.behavioral_lock = behavioral_lock or BehavioralLock()
        self.camera_service = (
            camera_service or CameraEvidenceService()
        )
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
        """Validate and return the 12-value Member 3 feature vector."""

        if not isinstance(features, (list, tuple)):
            raise ValueError(
                "Feature window must be a list or tuple."
            )

        if len(features) != len(FEATURE_ORDER):
            raise ValueError(
                f"Feature window must contain "
                f"{len(FEATURE_ORDER)} values."
            )

        try:
            return [float(value) for value in features]
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Feature window contains an invalid value."
            ) from error

    def start_session(self, user_id):
        """Create a database session."""

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
        Process one behavioural feature window.

        CRITICAL flow:

            ML
            -> Risk
            -> Response
            -> Save Risk Event
            -> Capture encrypted webcam photo
            -> Save evidence metadata
            -> Activate Sentinel lock
            -> Lock Windows

        The camera capture happens BEFORE Windows LockWorkStation()
        so the webcam can still be accessed.
        """

        vector = self.flatten_features(features)

        # --------------------------------------------------
        # 1. Member 3: Behavioural ML
        # --------------------------------------------------

        ml_output = self.analyzer.analyze_for_risk_engine(
            vector
        )

        # --------------------------------------------------
        # 2. Member 4: Risk Engine
        # --------------------------------------------------

        risk_result = self.risk_engine.calculate_risk(
            ml_output
        )

        # --------------------------------------------------
        # 3. Member 4: Response Engine
        # --------------------------------------------------

        response = self.response_engine.determine_action(
            risk_result
        )

        captured_at = datetime.utcnow()

        # --------------------------------------------------
        # 4. DATABASE PERSISTENCE
        # --------------------------------------------------

        risk_event_id = None

        if self.session_factory is not None:
            risk_event_id = self._persist_result(
                session_id=session_id,
                ml_output=ml_output,
                risk_result=risk_result,
                response=response,
                timestamp=captured_at,
            )

        # --------------------------------------------------
        # 5. CRITICAL RESPONSE
        # --------------------------------------------------

        if response["lock_required"]:

            print()
            print("=" * 60)
            print("SENTINEL CRITICAL RESPONSE")
            print("=" * 60)

            # --------------------------------------------------
            # Activate Sentinel lock FIRST.
            # --------------------------------------------------

            self.behavioral_lock.lock()

            print("Sentinel behavioral lock activated.")

            # --------------------------------------------------
            # CAMERA EVIDENCE
            #
            # MUST happen before Windows is locked.
            # --------------------------------------------------

            evidence_path = None

            try:

                print("Capturing security evidence...")

                evidence_path = (
                    self.camera_service.capture_encrypted_image(
                        captured_at
                    )
                )

                if evidence_path is not None:

                    print(
                        "Encrypted camera evidence captured:"
                    )
                    print(f"  {evidence_path}")

                else:

                    print(
                        "WARNING: Camera evidence could not "
                        "be captured."
                    )

            except Exception as error:

                # Camera failure must NOT prevent the
                # behavioral lock.

                print(
                    "WARNING: Camera capture failed:"
                )
                print(f"  {error}")

            # --------------------------------------------------
            # SAVE EVIDENCE METADATA
            # --------------------------------------------------

            if (
                evidence_path is not None
                and self.session_factory is not None
                and session_id is not None
                and risk_event_id is not None
            ):

                try:

                    self._persist_evidence(
                        session_id=session_id,
                        risk_event_id=risk_event_id,
                        timestamp=captured_at,
                        file_reference=evidence_path,
                    )

                    print(
                        "Camera evidence registered in database."
                    )

                except Exception as error:

                    print(
                        "WARNING: Evidence database "
                        f"registration failed: {error}"
                    )

            # --------------------------------------------------
            # WINDOWS LOCK
            #
            # This is LAST because camera capture must happen
            # before Windows moves to the secure desktop.
            # --------------------------------------------------

            print("Locking Windows session...")

            response["windows_locked"] = (
                self.behavioral_lock.lock_windows_session()
            )

            if response["windows_locked"]:

                print("Windows session locked.")

            else:

                print(
                    "WARNING: Windows session could not "
                    "be locked."
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
                confidence_score=(
                    ml_output["legitimate_confidence"]
                ),
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
                        f"Behavioural response: "
                        f"{response['action']}"
                    ),
                    status=(
                        "OPEN"
                        if response["risk_level"] != "LOW"
                        else "RESOLVED"
                    ),
                )
            )

            db.commit()

            return risk_event.id

    def _persist_evidence(
        self,
        session_id,
        risk_event_id,
        timestamp,
        file_reference,
    ):
        from src.local_agent.database.models import Evidence

        with self.session_factory() as db:

            evidence = Evidence(
                session_id=session_id,
                risk_event_id=risk_event_id,
                timestamp=timestamp,
                evidence_type="WEBCAM_IMAGE",
                file_reference=str(file_reference),
                encryption_status="FERNET",
                expires_at=None,
            )

            db.add(evidence)
            db.commit()

    def end_session(self, session_id):
        """Close an active Sentinel monitoring session."""

        if self.session_factory is None:
            return

        from src.local_agent.database.models import Session

        with self.session_factory() as db:
            session = db.query(Session).filter(
                Session.id == session_id
            ).first()

            if session is not None:
                session.status = "ENDED"
                db.commit()