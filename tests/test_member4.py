from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.local_agent.camera.evidence import CameraEvidenceService
from src.local_agent.integration.pipeline import SentinelPipeline
from src.local_agent.response.behavioral_lock import BehavioralLock
from src.local_agent.response.response_engine import ResponseEngine
from src.local_agent.risk.risk_engine import RiskEngine


def payload(score, confidence, recent=None, count=0, repeated=False, learning=True):
    return {"anomaly_score": score, "legitimate_confidence": confidence,
            "is_deviation": score >= .3, "recent_anomaly_average": score if recent is None else recent,
            "consecutive_deviation_count": count, "has_repeated_deviation": repeated,
            "model_state": "SUSPICIOUS" if score >= .3 else "LEGITIMATE",
            "profile_update_allowed": learning}


@pytest.mark.parametrize(("data", "level", "action"), [
    (payload(.05, .95), "LOW", "CONTINUE"),
    (payload(.50, .50, count=1), "MEDIUM", "INCREASE_MONITORING"),
    (payload(.82, .18, .74, 3, True), "HIGH", "RESTRICT"),
    (payload(.98, .02, .90, 5, True), "CRITICAL", "BEHAVIORAL_LOCK"),
])
def test_risk_response_levels(data, level, action):
    risk = RiskEngine().calculate_risk(data)
    response = ResponseEngine().determine_action(risk)
    assert risk["risk_level"] == level
    assert response["action"] == action
    if level in ("HIGH", "CRITICAL"):
        assert response["profile_update_allowed"] is False


def test_member3_recent_average_is_not_replaced():
    result = RiskEngine().calculate_risk(payload(.82, .18, recent=.74, count=3, repeated=True))
    assert result["recent_anomaly_risk"] == 74.0


def test_behavioral_lock_only_recovers_after_authorization(monkeypatch):
    lock = BehavioralLock()
    lock.lock()
    monkeypatch.setattr(lock.access_controller, "authorize_behavioral_lock_recovery", lambda **_: SimpleNamespace(allowed=False))
    assert lock.recover("admin", "wrong") is False and lock.is_locked()
    monkeypatch.setattr(lock.access_controller, "authorize_behavioral_lock_recovery", lambda **_: SimpleNamespace(allowed=True))
    assert lock.recover("admin", "correct") is True and not lock.is_locked()


def test_evidence_expiry_and_delete():
    storage_dir = Path("tests/.runtime_evidence")
    storage_dir.mkdir(exist_ok=True)
    service = CameraEvidenceService(storage_dir=storage_dir, retention_days=30)
    captured_at = datetime(2026, 1, 1)
    assert service.expires_at(captured_at) == captured_at + timedelta(days=30)
    encrypted = storage_dir / "image.jpg.fernet"; encrypted.write_bytes(b"encrypted")
    service.delete_file(encrypted)
    assert not encrypted.exists()
    storage_dir.rmdir()


class FakeDatabase:
    def __init__(self): self.added = []; self.committed = False
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def add(self, value): self.added.append(value)
    def flush(self): self.added[0].id = 99
    def commit(self): self.committed = True


class FakeAnalyzer:
    def analyze_for_risk_engine(self, vector):
        assert len(vector) == 12
        return payload(.82, .18, .74, 3, True, False)


class FakeCamera:
    def capture_encrypted_image(self, timestamp): return Path("data/evidence/test.jpg.fernet")
    def expires_at(self, timestamp): return timestamp + timedelta(days=30)


def test_pipeline_persists_high_risk_and_evidence(monkeypatch):
    import src.local_agent.integration.pipeline as module
    database = FakeDatabase()
    monkeypatch.setattr(module, "SessionLocal", lambda: database)
    pipeline = SentinelPipeline(analyzer=FakeAnalyzer(), camera_service=FakeCamera())
    features = {"keyboard": {"average_hold_time": 0, "average_flight_time": 0, "typing_speed": 0, "average_pause_duration": 0, "correction_rate": 0}, "mouse": {"average_speed": 0, "average_distance": 0, "average_click_duration": 0, "average_acceleration": 0, "direction_changes": 0, "click_rate": 0, "idle_ratio": 0}}
    result = pipeline.process_features(7, features)
    assert result["response"]["action"] == "RESTRICT"
    assert database.committed and len(database.added) == 3
    assert database.added[-1].evidence_type == "WEBCAM_IMAGE"
