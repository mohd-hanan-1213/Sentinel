from risk.risk_engine import RiskEngine


def test_case(name, ml_output):
    engine = RiskEngine()

    result = engine.calculate_risk(ml_output)

    print("\n" + "=" * 50)
    print(name)
    print("=" * 50)

    print("Risk Score :", result["risk_score"])
    print("Risk Level :", result["risk_level"])
    print("Model State:", result["model_state"])
    print("Profile Update Allowed:",
          result["profile_update_allowed"])


# --------------------------------------------------
# TEST 1: NORMAL USER
# --------------------------------------------------

normal_user = {
    "anomaly_score": 0.10,
    "legitimate_confidence": 0.90,
    "is_deviation": False,
    "recent_anomaly_average": 0.12,
    "consecutive_deviation_count": 0,
    "has_repeated_deviation": False,
    "model_state": "NORMAL",
    "profile_update_allowed": True
}


# --------------------------------------------------
# TEST 2: MODERATE DEVIATION
# --------------------------------------------------

moderate_deviation = {
    "anomaly_score": 0.45,
    "legitimate_confidence": 0.55,
    "is_deviation": True,
    "recent_anomaly_average": 0.40,
    "consecutive_deviation_count": 1,
    "has_repeated_deviation": False,
    "model_state": "SUSPICIOUS",
    "profile_update_allowed": False
}


# --------------------------------------------------
# TEST 3: REPEATED DEVIATION
# --------------------------------------------------

repeated_deviation = {
    "anomaly_score": 0.70,
    "legitimate_confidence": 0.30,
    "is_deviation": True,
    "recent_anomaly_average": 0.65,
    "consecutive_deviation_count": 3,
    "has_repeated_deviation": True,
    "model_state": "SUSPICIOUS",
    "profile_update_allowed": False
}


# --------------------------------------------------
# TEST 4: VERY HIGH / POTENTIAL TAKEOVER
# --------------------------------------------------

high_risk = {
    "anomaly_score": 0.95,
    "legitimate_confidence": 0.05,
    "is_deviation": True,
    "recent_anomaly_average": 0.90,
    "consecutive_deviation_count": 5,
    "has_repeated_deviation": True,
    "model_state": "SUSPICIOUS",
    "profile_update_allowed": False
}

# --------------------------------------------------
# TEST 5: MEMBER 3 ACTUAL ML OUTPUT
# --------------------------------------------------

member3_output = {
    "anomaly_score": 0.82,
    "legitimate_confidence": 0.18,
    "is_deviation": True,
    "recent_anomaly_average": 0.74,
    "consecutive_deviation_count": 3,
    "has_repeated_deviation": True,
    "model_state": "SUSPICIOUS",
    "profile_update_allowed": False
}

# --------------------------------------------------
# RUN TESTS
# --------------------------------------------------

test_case("NORMAL USER", normal_user)
test_case("MODERATE DEVIATION", moderate_deviation)
test_case("REPEATED DEVIATION", repeated_deviation)
test_case("HIGH RISK", high_risk)
test_case("MEMBER 3 ACTUAL OUTPUT", member3_output)