"""The runtime boundary joining Member 2, Member 3, and Member 4."""

from datetime import datetime

from sqlalchemy import select

from src.local_agent.camera.evidence import CameraEvidenceService
from src.local_agent.database.connection import SessionLocal
from src.local_agent.database.models import Evidence, RiskEvent, SecurityEvent, Session
from src.local_agent.response.behavioral_lock import BehavioralLock
from src.local_agent.response.response_engine import ResponseEngine
from src.local_agent.risk.risk_engine import RiskEngine


FEATURE_ORDER = (
    "keyboard.average_hold_time", "keyboard.average_flight_time",
    "keyboard.typing_speed", "keyboard.average_pause_duration",
    "keyboard.correction_rate", "mouse.average_speed",
    "mouse.average_distance", "mouse.average_click_duration",
    "mouse.average_acceleration", "mouse.direction_changes",
    "mouse.click_rate", "mouse.idle_ratio",
)


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
            from src.ml.behavior_authenticator import BehaviorAuthenticator
        except ImportError as error:
            raise RuntimeError(
                "Member 3 ML module is not available. Merge origin/ml_model "
                "before starting the Sentinel pipeline."
            ) from error
        return BehaviorAuthenticator()

    @staticmethod
    def flatten_features(features):
        try:
            return [float(features[group][name]) for group, name in
                    (item.split('.', 1) for item in FEATURE_ORDER)]
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Feature window does not meet the Member 3 contract.") from error

    def start_session(self, user_id):
        with SessionLocal() as db:
            session = Session(user_id=user_id, status="ACTIVE")
            db.add(session)
            db.commit()
            return session.id

    def process_features(self, session_id, features):
        vector = self.flatten_features(features)
        ml_output = self.analyzer.analyze_for_risk_engine(vector)
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

    def purge_expired_evidence(self, now=None):
        now = now or datetime.utcnow()
        removed = 0
        with SessionLocal() as db:
            expired = db.scalars(select(Evidence).where(Evidence.expires_at <= now)).all()
            for evidence in expired:
                self.camera_service.delete_file(evidence.file_reference)
                db.delete(evidence)
                removed += 1
            db.commit()
        return removed

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
            encryption_status="FERNET", expires_at=self.camera_service.expires_at(timestamp),
        ))
