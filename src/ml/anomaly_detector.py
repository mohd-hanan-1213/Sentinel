from src.ml.confidence_calculator import (
    calculate_confidence_scores,
)
from src.ml.feature_contract import validate_feature_vector
from src.ml.model_manager import (
    load_model_bundle,
    validate_model_bundle,
)


def detect_anomaly(
    feature_vector,
    model_bundle=None,
    model_path=None,
):
    """
    Score one behavioural feature vector with a trained model.
    """

    if model_bundle is None:
        model_bundle = load_model_bundle(model_path)
    else:
        validate_model_bundle(model_bundle)

    validated_vector = validate_feature_vector(feature_vector)

    scaled_vector = model_bundle["scaler"].transform(
        [validated_vector]
    )

    raw_score = float(
        model_bundle["model"].decision_function(
            scaled_vector
        )[0]
    )

    prediction = int(
        model_bundle["model"].predict(
            scaled_vector
        )[0]
    )

    scores = calculate_confidence_scores(raw_score)

    return {
        "anomaly_score": scores["anomaly_score"],
        "legitimate_confidence": (
            scores["legitimate_confidence"]
        ),
        "is_deviation": prediction == -1,
        "raw_score": raw_score,
        "prediction": prediction,
        "model_type": model_bundle["model_type"],
    }
