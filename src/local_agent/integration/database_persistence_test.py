from src.local_agent.integration.pipeline import SentinelPipeline
from src.local_agent.database.connection import SessionLocal
from src.local_agent.database.models import Session, RiskEvent, SecurityEvent


def main():
    print("=" * 60)
    print("SENTINEL DATABASE PERSISTENCE TEST")
    print("=" * 60)

    # Use the existing Sentinel admin/user.
    with SessionLocal() as db:
        user = db.query(
            __import__(
                "src.local_agent.database.models",
                fromlist=["User"]
            ).User
        ).filter_by(username="aswinKB").first()

        if user is None:
            raise RuntimeError("Sentinel user 'aswinKB' was not found.")

        user_id = user.id

    pipeline = SentinelPipeline(
        analyzer=TestAnalyzer(),
        session_factory=SessionLocal,
    )

    print("\n[TEST 1] Create session")
    session_id = pipeline.start_session(user_id)
    print("Session ID:", session_id)
    assert session_id is not None

    print("\n[TEST 2] Process feature window")

    features = [0.1] * 12

    result = pipeline.process_features(
        session_id=session_id,
        features=features,
    )

    print("Risk level:", result["risk"]["risk_level"])
    print("Risk score:", result["risk"]["risk_score"])
    print("Response:", result["response"]["action"])

    print("\n[TEST 3] Verify database records")

    with SessionLocal() as db:
        session = db.get(Session, session_id)

        risk_event = (
            db.query(RiskEvent)
            .filter_by(session_id=session_id)
            .order_by(RiskEvent.id.desc())
            .first()
        )

        security_event = (
            db.query(SecurityEvent)
            .filter_by(session_id=session_id)
            .order_by(SecurityEvent.id.desc())
            .first()
        )

        assert session is not None
        assert risk_event is not None
        assert security_event is not None

        print("Session record      : FOUND")
        print("RiskEvent record    : FOUND")
        print("SecurityEvent record: FOUND")

        print("\nStored RiskEvent:")
        print("  Risk score :", risk_event.risk_score)
        print("  Risk level :", risk_event.risk_level)
        print("  Response   :", risk_event.response)

        print("\nStored SecurityEvent:")
        print("  Event type :", security_event.event_type)
        print("  Severity   :", security_event.severity)
        print("  Status     :", security_event.status)

    print("\n" + "=" * 60)
    print("DATABASE PERSISTENCE TEST PASSED")
    print("=" * 60)


class TestAnalyzer:
    """Deterministic ML output for persistence testing."""

    def analyze_for_risk_engine(self, feature_vector):
        return {
            "anomaly_score": 0.1,
            "legitimate_confidence": 0.9,
            "is_deviation": False,
            "recent_anomaly_average": 0.1,
            "consecutive_deviation_count": 0,
            "has_repeated_deviation": False,
            "profile_update_allowed": True,
            "model_state": "ACTIVE",
        }


if __name__ == "__main__":
    main()