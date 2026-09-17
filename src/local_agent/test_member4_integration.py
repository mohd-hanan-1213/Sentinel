from risk.risk_engine import RiskEngine
from response.response_engine import ResponseEngine
from response.behavioral_lock import BehavioralLock


def print_result(title, risk_result, response_result):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    print(f"Risk Score          : {risk_result['risk_score']}")
    print(f"Risk Level          : {risk_result['risk_level']}")
    print(f"Action              : {response_result['action']}")
    print(f"Lock Required       : {response_result['lock_required']}")
    print(f"Monitoring Level    : {response_result['monitoring_level']}")
    print(f"Profile Update      : {response_result['profile_update_allowed']}")


def main():
    print("=" * 60)
    print("SENTINEL MEMBER 4 FINAL INTEGRATION TEST")
    print("=" * 60)

    risk_engine = RiskEngine()
    response_engine = ResponseEngine()
    behavioral_lock = BehavioralLock()

    # ---------------------------------------------------------
    # TEST 1: NORMAL BEHAVIOUR
    # ---------------------------------------------------------
    normal_ml_output = {
        "anomaly_score": 0.05,
        "legitimate_confidence": 0.95,
        "is_deviation": False,
        "recent_anomaly_average": 0.05,
        "consecutive_deviation_count": 0,
        "has_repeated_deviation": False,
        "model_state": "LEGITIMATE",
        "profile_update_allowed": True,
    }

    risk_result = risk_engine.calculate_risk(normal_ml_output)
    response_result = response_engine.determine_action(risk_result)

    print_result("TEST 1: NORMAL BEHAVIOUR", risk_result, response_result)

    assert risk_result["risk_level"] == "LOW"
    assert response_result["action"] == "CONTINUE"
    assert response_result["lock_required"] is False
    assert response_result["profile_update_allowed"] is True
    assert behavioral_lock.is_locked() is False

    print("PASS")

    # ---------------------------------------------------------
    # TEST 2: MEDIUM RISK
    # ---------------------------------------------------------
    medium_ml_output = {
        "anomaly_score": 0.50,
        "legitimate_confidence": 0.50,
        "is_deviation": True,
        "recent_anomaly_average": 0.50,
        "consecutive_deviation_count": 1,
        "has_repeated_deviation": False,
        "model_state": "UNCERTAIN",
        "profile_update_allowed": False,
    }

    risk_result = risk_engine.calculate_risk(medium_ml_output)
    response_result = response_engine.determine_action(risk_result)

    print_result("TEST 2: MEDIUM RISK", risk_result, response_result)

    assert risk_result["risk_level"] == "MEDIUM"
    assert response_result["action"] == "INCREASE_MONITORING"
    assert response_result["monitoring_level"] == "ELEVATED"
    assert response_result["lock_required"] is False

    print("PASS")

    # ---------------------------------------------------------
    # TEST 3: HIGH RISK
    # ---------------------------------------------------------
    high_ml_output = {
        "anomaly_score": 0.82,
        "legitimate_confidence": 0.18,
        "is_deviation": True,
        "recent_anomaly_average": 0.74,
        "consecutive_deviation_count": 3,
        "has_repeated_deviation": True,
        "model_state": "SUSPICIOUS",
        "profile_update_allowed": True,
    }

    risk_result = risk_engine.calculate_risk(high_ml_output)
    response_result = response_engine.determine_action(risk_result)

    print_result("TEST 3: HIGH RISK", risk_result, response_result)

    assert risk_result["risk_level"] == "HIGH"
    assert response_result["action"] == "RESTRICT"
    assert response_result["monitoring_level"] == "HIGH"
    assert response_result["lock_required"] is False

    # Suspicious behaviour must not update the profile.
    assert risk_result["profile_update_allowed"] is False
    assert response_result["profile_update_allowed"] is False

    print("PASS")

    # ---------------------------------------------------------
    # TEST 4: CRITICAL RISK
    # ---------------------------------------------------------
    critical_ml_output = {
        "anomaly_score": 0.98,
        "legitimate_confidence": 0.02,
        "is_deviation": True,
        "recent_anomaly_average": 0.90,
        "consecutive_deviation_count": 5,
        "has_repeated_deviation": True,
        "model_state": "SUSPICIOUS",
        "profile_update_allowed": True,
    }

    risk_result = risk_engine.calculate_risk(critical_ml_output)
    response_result = response_engine.determine_action(risk_result)

    print_result("TEST 4: CRITICAL RISK", risk_result, response_result)

    assert risk_result["risk_level"] == "CRITICAL"
    assert response_result["action"] == "BEHAVIORAL_LOCK"
    assert response_result["monitoring_level"] == "CRITICAL"
    assert response_result["lock_required"] is True

    # Suspicious behaviour must never update the profile.
    assert risk_result["profile_update_allowed"] is False
    assert response_result["profile_update_allowed"] is False

    print("PASS")

    # ---------------------------------------------------------
    # TEST 5: ACTIVATE BEHAVIOURAL LOCK
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("TEST 5: ACTIVATE BEHAVIOURAL LOCK")
    print("=" * 60)

    if response_result["lock_required"]:
        behavioral_lock.lock()

    print(f"Lock State : {behavioral_lock.get_state()}")
    print(f"Locked     : {behavioral_lock.is_locked()}")

    assert behavioral_lock.is_locked() is True

    print("PASS")

    # ---------------------------------------------------------
    # TEST 6: FAILED RECOVERY
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("TEST 6: FAILED SENTINEL RECOVERY")
    print("=" * 60)

    wrong_username = "invalid_user"
    wrong_password = "invalid_password"

    recovery_result = behavioral_lock.recover(
        wrong_username,
        wrong_password
    )

    print(f"Recovery successful : {recovery_result}")
    print(f"Lock State          : {behavioral_lock.get_state()}")
    print(f"Locked              : {behavioral_lock.is_locked()}")

    assert recovery_result is False
    assert behavioral_lock.is_locked() is True

    print("PASS")

    # ---------------------------------------------------------
    # TEST 7: SUCCESSFUL SENTINEL RECOVERY
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("TEST 7: SUCCESSFUL SENTINEL RECOVERY")
    print("=" * 60)

    username = input("Enter Sentinel admin username: ")
    password = input("Enter Sentinel admin password: ")

    recovery_result = behavioral_lock.recover(
        username,
        password
    )

    print(f"Recovery successful : {recovery_result}")
    print(f"Lock State          : {behavioral_lock.get_state()}")
    print(f"Locked              : {behavioral_lock.is_locked()}")

    assert recovery_result is True
    assert behavioral_lock.is_locked() is False

    print("PASS")

    # ---------------------------------------------------------
    # TEST 8: FINAL SECURITY STATE
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("TEST 8: FINAL SECURITY STATE")
    print("=" * 60)

    assert behavioral_lock.is_locked() is False
    assert response_result["profile_update_allowed"] is False

    print("Behavioral lock     : RECOVERED")
    print("Suspicious profile  : UPDATE BLOCKED")
    print("Security response   : VERIFIED")

    print("\nPASS")

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("ALL MEMBER 4 INTEGRATION TESTS PASSED")
    print("=" * 60)

    print("\nMember 4 pipeline verified:")
    print("ML Output")
    print("    ↓")
    print("Risk Engine")
    print("    ↓")
    print("Response Engine")
    print("    ↓")
    print("Security Response")
    print("    ↓")
    print("Behavioral Lock")
    print("    ↓")
    print("Sentinel Authentication")
    print("    ↓")
    print("Recovery")


if __name__ == "__main__":
    main()