"""The runtime boundary joining Member 2, Member 3, and Member 4."""

from datetime import datetime

from src.local_agent.camera.evidence import CameraEvidenceService
from src.local_agent.database.connection import SessionLocal
from src.local_agent.database.models import Evidence, RiskEvent, SecurityEvent, Session
from src.local_agent.response.behavioral_lock import BehavioralLock
from src.local_agent.response.response_engine import ResponseEngine
from src.local_agent.risk.risk_engine import RiskEngine
from src.ml.authentication_pipeline import MODE_ACTIVE, MODE_ENROLMENT
from src.ml.feature_contract import flatten_feature_dict, validate_feature_vector


ENROLMENT_RESPONSE = "ENROLMENT_IN_PROGRESS"


class SentinelPipeline:
    """Process one behavioural feature window into persisted security action."""

    def __init__(self, analyzer=None, risk_engine=None, response_engine=None,
                 behavioral_lock=None, camera_service=None):
        self.analyzer = analyzer or self._load_member3_analyzer()
        self.risk_engine = risk_engine or RiskEngine()
        self.response_engine = response_engine or ResponseEngine()
        self.behavioral_lock = behavioral_lock or BehavioralLock()
        self.camera_service = camera_service or CameraEvidenceService()

    @staticmethod
    def _load_member3_analyzer():
        try:
            from src.ml.authentication_pipeline import AuthenticationPipeline
        except ImportError as error:
            raise RuntimeError(
                "Member 3 ML module is not available. Merge origin/ml_model "
                "before starting the Sentinel pipeline."
            ) from error
        return AuthenticationPipeline()

    @staticmethod
    def flatten_features(features):
        if isinstance(features, (list, tuple)):
            return validate_feature_vector(features)

        if isinstance(features, dict):
            return flatten_feature_dict(features)

        raise ValueError("Feature window does not meet the Member 3 contract.")

    def start_session(self, user_id):
        with SessionLocal() as db:
            session = Session(user_id=user_id, status="ACTIVE")
            db.add(session)
            db.commit()
            return session.id

    def process_features(self, session_id, features):
        vector = self.flatten_features(features)
        ml_output = self._process_with_member3(vector)

        if ml_output.get("mode") == MODE_ENROLMENT:
            return self._build_enrolment_output(ml_output)

        if ml_output.get("mode") == MODE_ACTIVE and ml_output.get("model_trained"):
            return self._build_model_ready_output(ml_output)

        risk_result = self.risk_engine.calculate_risk(ml_output)
        response = self.response_engine.determine_action(risk_result)
        captured_at = datetime.utcnow()

        with SessionLocal() as db:
            risk_event = RiskEvent(
                session_id=session_id, timestamp=captured_at,
                anomaly_score=ml_output["anomaly_score"],
                confidence_score=ml_output["legitimate_confidence"],
                risk_score=risk_result["risk_score"],
                risk_level=risk_result["risk_level"], event_type="BEHAVIORAL_ANALYSIS",
                response=response["action"],
            )
            db.add(risk_event)
            db.flush()
            self._record_response(db, session_id, response, captured_at)
            if response["risk_level"] in ("HIGH", "CRITICAL"):
                self._capture_evidence(db, session_id, risk_event.id, captured_at)
            db.commit()

        if response["lock_required"]:
            self.behavioral_lock.lock()
            response["windows_locked"] = self.behavioral_lock.lock_windows_session()
        else:
            response["windows_locked"] = False
        return {"ml_output": ml_output, "risk": risk_result, "response": response}

    def _process_with_member3(self, vector):
        if hasattr(self.analyzer, "process_feature_vector"):
            return self.analyzer.process_feature_vector(vector)

        if hasattr(self.analyzer, "analyze_for_risk_engine"):
            return self.analyzer.analyze_for_risk_engine(vector)

        raise RuntimeError(
            "Member 3 analyzer must provide process_feature_vector() "
            "or analyze_for_risk_engine()."
        )

    @staticmethod
    def _build_enrolment_output(ml_output):
        response = {
            "action": ENROLMENT_RESPONSE,
            "risk_level": MODE_ENROLMENT,
            "lock_required": False,
            "windows_locked": False,
            "profile_update_allowed": True,
        }

        return {
            "ml_output": ml_output,
            "risk": None,
            "response": response,
        }

    @staticmethod
    def _build_model_ready_output(ml_output):
        response = {
            "action": "MODEL_TRAINED",
            "risk_level": MODE_ACTIVE,
            "lock_required": False,
            "windows_locked": False,
            "profile_update_allowed": False,
        }

        return {
            "ml_output": ml_output,
            "risk": None,
            "response": response,
        }

    @staticmethod
    def _record_response(db, session_id, response, timestamp):
        db.add(SecurityEvent(
            session_id=session_id, timestamp=timestamp,
            event_type=response["action"], severity=response["risk_level"],
            description=f"Behavioural response: {response['action']}",
            status="OPEN" if response["risk_level"] != "LOW" else "RESOLVED",
        ))

    def _capture_evidence(self, db, session_id, risk_event_id, timestamp):
        try:
            encrypted_path = self.camera_service.capture_encrypted_image(timestamp)
        except (ImportError, OSError):
            encrypted_path = None
        if encrypted_path is None:
            return
        db.add(Evidence(
            session_id=session_id, risk_event_id=risk_event_id, timestamp=timestamp,
            evidence_type="WEBCAM_IMAGE", file_reference=str(encrypted_path),
            encryption_status="FERNET", expires_at=None,
        ))
