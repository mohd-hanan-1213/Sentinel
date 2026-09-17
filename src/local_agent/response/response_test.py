from response.response_engine import ResponseEngine


def test_case(name, risk_result):
    engine = ResponseEngine()

    result = engine.determine_action(risk_result)

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    print("Risk Score          :", result["risk_score"])
    print("Risk Level          :", result["risk_level"])
    print("Action              :", result["action"])
    print("Lock Required       :", result["lock_required"])
    print("Monitoring Level    :", result["monitoring_level"])
    print("Profile Update      :", result["profile_update_allowed"])


# --------------------------------------------------
# TEST 1: LOW
# --------------------------------------------------

low_risk = {
    "risk_score": 8.5,
    "risk_level": "LOW",
    "profile_update_allowed": True,
}


# --------------------------------------------------
# TEST 2: MEDIUM
# --------------------------------------------------

medium_risk = {
    "risk_score": 41.25,
    "risk_level": "MEDIUM",
    "profile_update_allowed": False,
}


# --------------------------------------------------
# TEST 3: HIGH
# --------------------------------------------------

high_risk = {
    "risk_score": 78.7,
    "risk_level": "HIGH",
    "profile_update_allowed": False,
}


# --------------------------------------------------
# TEST 4: CRITICAL
# --------------------------------------------------

critical_risk = {
    "risk_score": 95.75,
    "risk_level": "CRITICAL",
    "profile_update_allowed": False,
}


# --------------------------------------------------
# TEST 5: HIGH WITH PROFILE UPDATE TRUE
# SECURITY TEST
# --------------------------------------------------

high_with_learning = {
    "risk_score": 75.0,
    "risk_level": "HIGH",
    "profile_update_allowed": True,
}


# --------------------------------------------------
# RUN TESTS
# --------------------------------------------------

test_case("LOW RISK", low_risk)
test_case("MEDIUM RISK", medium_risk)
test_case("HIGH RISK", high_risk)
test_case("CRITICAL RISK", critical_risk)
test_case(
    "HIGH RISK WITH PROFILE UPDATE TRUE",
    high_with_learning,
)