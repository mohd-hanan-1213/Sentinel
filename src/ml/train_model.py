from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.ml.feature_contract import (
    FEATURE_NAMES,
    validate_feature_vector,
)
from src.ml.profile_builder import MIN_ENROLLMENT_SAMPLES


DEFAULT_CONTAMINATION = 0.05
DEFAULT_RANDOM_STATE = 42


def train_isolation_forest(
    feature_vectors,
    contamination=DEFAULT_CONTAMINATION,
    random_state=DEFAULT_RANDOM_STATE,
    min_samples=MIN_ENROLLMENT_SAMPLES,
):
    """
    Train the first behavioural anomaly-detection pipeline.

    Training data should contain legitimate-user enrolment
    samples only. The scaler is model-specific and must be
    reused for future prediction.
    """

    validated_vectors = _validate_training_vectors(
        feature_vectors,
        min_samples,
    )

    scaler = StandardScaler()
    scaled_vectors = scaler.fit_transform(validated_vectors)

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
    )

    model.fit(scaled_vectors)

    return {
        "scaler": scaler,
        "model": model,
        "feature_names": list(FEATURE_NAMES),
        "sample_count": len(validated_vectors),
        "model_type": "IsolationForest",
        "contamination": contamination,
        "random_state": random_state,
    }


def _validate_training_vectors(
    feature_vectors,
    min_samples,
):

    if min_samples <= 0:
        raise ValueError(
            "Minimum training samples must be positive."
        )

    if feature_vectors is None:
        raise ValueError(
            "Training feature vectors are required."
        )

    validated_vectors = [
        validate_feature_vector(feature_vector)
        for feature_vector in feature_vectors
    ]

    if len(validated_vectors) < min_samples:
        raise ValueError(
            "Not enough legitimate samples for training. "
            f"Required: {min_samples}, "
            f"received: {len(validated_vectors)}."
        )

    return validated_vectors
