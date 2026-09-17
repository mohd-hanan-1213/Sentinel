from src.ml.mock_data_generator import generate_legitimate_sample
from src.ml.train_model import train_isolation_forest
from src.ml.behavior_authenticator import BehaviorAuthenticator

from src.local_agent.integration.pipeline import SentinelPipeline
from src.local_agent.response.behavioral_lock import BehavioralLock


class TestAccessController:
    """
    Test-only access controller.

    The real AccessController remains database-backed.
    This object only allows us to test the behavioral lock
    state transition without PostgreSQL.
    """

    def authorize_behavioral_lock_recovery(
        self,
        username,
        password,
    ):
        class Result:
            allowed = True

        return Result()


class TestWindowsLock:
    """
    Test-only Windows lock implementation.

    Prevents the test from actually locking the computer.
    """

    def __init__(self):
        self.windows_lock_called = False

    def lock_windows_session(self):
        self.windows_lock_called = True
        return True


class CriticalTestAnalyzer:
    """
    Test-only analyzer that deliberately produces
    a CRITICAL-risk ML result.
    """

    def analyze_for_risk_engine(self, feature_vector):
        return {
            "anomaly_score": 1.0,
            "legitimate_confidence": 0.0,
            "is_deviation": True,
            "recent_anomaly_average": 1.0,
            "consecutive_deviation_count": 5,
            "has_repeated_deviation": True,
            "profile_update_allowed": False,
            "model_state": "FROZEN",
        }


def test_normal_pipeline():
    print("\n")
    print("=" * 60)
    print("TEST 1: NORMAL ML -> RISK -> RESPONSE")
    print("=" * 60)

    # --------------------------------------------------
    # Generate legitimate training data
    # --------------------------------------------------

    training_samples = [
        generate_legitimate_sample()
        for _ in range(30)
    ]

    print("Training samples:", len(training_samples))

    # --------------------------------------------------
    # Train temporary Member 3 model
    # --------------------------------------------------

    model_bundle = train_isolation_forest(training_samples)

    print("Model type:", model_bundle["model_type"])
    print("Model samples:", model_bundle["sample_count"])

    # --------------------------------------------------
    # Create Member 3 analyzer
    # --------------------------------------------------

    analyzer = BehaviorAuthenticator(
        model_bundle=model_bundle
    )

    # --------------------------------------------------
    # Create test behavioral lock
    # --------------------------------------------------

    test_access_controller = TestAccessController()

    behavioral_lock = BehavioralLock(
        access_controller=test_access_controller
    )

    # --------------------------------------------------
    # Create complete pipeline
    # --------------------------------------------------

    pipeline = SentinelPipeline(
        analyzer=analyzer,
        behavioral_lock=behavioral_lock,
        session_factory=None,
    )

    print("Pipeline initialized.")

    # --------------------------------------------------
    # Process legitimate feature vector
    # --------------------------------------------------

    feature_vector = generate_legitimate_sample()

    print("\nFeature vector:")
    print(feature_vector)

    result = pipeline.process_features(
        session_id=None,
        features=feature_vector,
    )

    print("\n--- ML OUTPUT ---")
    print(result["ml_output"])

    print("\n--- RISK RESULT ---")
    print(result["risk"])

    print("\n--- RESPONSE ---")
    print(result["response"])

    print("\n--- BEHAVIORAL LOCK ---")
    print(
        "Lock state:",
        pipeline.behavioral_lock.get_state()
    )

    print(
        "Is locked:",
        pipeline.behavioral_lock.is_locked()
    )

    assert result["response"]["lock_required"] is False
    assert result["response"]["windows_locked"] is False
    assert pipeline.behavioral_lock.is_locked() is False

    print("\nNORMAL PIPELINE TEST PASSED.")


def test_critical_pipeline():
    print("\n")
    print("=" * 60)
    print("TEST 2: CRITICAL -> BEHAVIORAL LOCK")
    print("=" * 60)

    # --------------------------------------------------
    # Create fake analyzer producing CRITICAL risk
    # --------------------------------------------------

    analyzer = CriticalTestAnalyzer()

    # --------------------------------------------------
    # Create behavioral lock
    # --------------------------------------------------

    behavioral_lock = BehavioralLock(
        access_controller=TestAccessController()
    )

    # Replace only the physical Windows-lock operation
    # with a safe test implementation.
    test_windows_lock = TestWindowsLock()

    behavioral_lock.lock_windows_session = (
        test_windows_lock.lock_windows_session
    )

    # --------------------------------------------------
    # Create pipeline
    # --------------------------------------------------

    pipeline = SentinelPipeline(
        analyzer=analyzer,
        behavioral_lock=behavioral_lock,
        session_factory=None,
    )

    # --------------------------------------------------
    # Process deliberately critical input
    # --------------------------------------------------

    feature_vector = [0.0] * 12

    result = pipeline.process_features(
        session_id=None,
        features=feature_vector,
    )

    print("\n--- ML OUTPUT ---")
    print(result["ml_output"])

    print("\n--- RISK RESULT ---")
    print(result["risk"])

    print("\n--- RESPONSE ---")
    print(result["response"])

    print("\n--- BEHAVIORAL LOCK ---")
    print(
        "Lock state:",
        pipeline.behavioral_lock.get_state()
    )

    print(
        "Is locked:",
        pipeline.behavioral_lock.is_locked()
    )

    print(
        "Windows lock requested:",
        test_windows_lock.windows_lock_called
    )

    # --------------------------------------------------
    # Verify CRITICAL behavior
    # --------------------------------------------------

    assert result["risk"]["risk_level"] == "CRITICAL"

    assert (
        result["response"]["action"]
        == "BEHAVIORAL_LOCK"
    )

    assert result["response"]["lock_required"] is True

    assert (
        pipeline.behavioral_lock.is_locked()
        is True
    )

    assert (
        test_windows_lock.windows_lock_called
        is True
    )

    assert (
        result["response"]["windows_locked"]
        is True
    )

    print("\nCRITICAL LOCK TEST PASSED.")


def main():
    print()
    print("SENTINEL FULL PIPELINE TEST")
    print("=" * 60)

    test_normal_pipeline()
    test_critical_pipeline()

    print()
    print("=" * 60)
    print("ALL FULL PIPELINE TESTS PASSED.")
    print("=" * 60)


if __name__ == "__main__":
    main()