from pathlib import Path

import joblib

from src.ml.feature_contract import FEATURE_NAMES


DEFAULT_MODEL_DIR = "models"
DEFAULT_MODEL_FILENAME = "sentinel_behavior_model.joblib"


REQUIRED_MODEL_BUNDLE_KEYS = [
    "scaler",
    "model",
    "feature_names",
    "sample_count",
    "model_type",
    "contamination",
    "random_state",
]


def save_model_bundle(model_bundle, model_path=None):
    """
    Save a trained model bundle and return the saved path.
    """

    validate_model_bundle(model_bundle)

    path = _resolve_model_path(model_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model_bundle, path)

    return str(path)


def load_model_bundle(model_path=None):
    """
    Load and validate a trained model bundle.
    """

    path = _resolve_model_path(model_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Model file does not exist: {path}"
        )

    model_bundle = joblib.load(path)

    validate_model_bundle(model_bundle)

    return model_bundle


def validate_model_bundle(model_bundle):
    """
    Confirm the model bundle has the expected structure.
    """

    if not isinstance(model_bundle, dict):
        raise ValueError(
            "Model bundle must be a dictionary."
        )

    missing_keys = [
        key
        for key in REQUIRED_MODEL_BUNDLE_KEYS
        if key not in model_bundle
    ]

    if missing_keys:
        raise ValueError(
            "Model bundle is missing required keys: "
            + ", ".join(missing_keys)
        )

    if model_bundle["feature_names"] != list(FEATURE_NAMES):
        raise ValueError(
            "Model bundle feature names do not match "
            "the current feature contract."
        )

    if model_bundle["sample_count"] <= 0:
        raise ValueError(
            "Model bundle sample count must be positive."
        )

    return True


def _resolve_model_path(model_path):

    if model_path is None:
        return Path(
            DEFAULT_MODEL_DIR,
            DEFAULT_MODEL_FILENAME,
        )

    return Path(model_path)
