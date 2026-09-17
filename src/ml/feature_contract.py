import math


KEYBOARD_FEATURES = [
    "average_hold_time",
    "average_flight_time",
    "typing_speed",
    "average_pause_duration",
    "correction_rate",
]


MOUSE_FEATURES = [
    "average_speed",
    "average_distance",
    "average_click_duration",
    "average_acceleration",
    "direction_changes",
    "click_rate",
    "idle_ratio",
]


FEATURE_NAMES = [
    *[
        f"keyboard.{feature_name}"
        for feature_name in KEYBOARD_FEATURES
    ],
    *[
        f"mouse.{feature_name}"
        for feature_name in MOUSE_FEATURES
    ],
]


FEATURE_COUNT = len(FEATURE_NAMES)


class FeatureContractError(ValueError):
    """
    Raised when a behavioural feature vector does not match
    the ML contract.
    """


def get_feature_names():
    """
    Return the fixed feature order expected by the ML model.
    """

    return list(FEATURE_NAMES)


def validate_feature_vector(feature_vector):
    """
    Validate a flattened feature vector.
    """

    if not isinstance(feature_vector, (list, tuple)):
        raise FeatureContractError(
            "Feature vector must be a list or tuple."
        )

    if len(feature_vector) != FEATURE_COUNT:
        raise FeatureContractError(
            f"Feature vector must contain {FEATURE_COUNT} values."
        )

    validated_vector = []

    for index, value in enumerate(feature_vector):

        if not _is_valid_number(value):
            feature_name = FEATURE_NAMES[index]

            raise FeatureContractError(
                f"Invalid value for {feature_name}: {value}"
            )

        validated_vector.append(float(value))

    return validated_vector


def flatten_feature_dict(features):
    """
    Convert nested Member 2 features into the fixed ML vector order.
    """

    if not isinstance(features, dict):
        raise FeatureContractError(
            "Features must be provided as a dictionary."
        )

    feature_vector = []

    for feature_name in FEATURE_NAMES:

        category, name = feature_name.split(".", 1)
        category_data = features.get(category)

        if not isinstance(category_data, dict):
            raise FeatureContractError(
                f"Missing feature category: {category}"
            )

        if name not in category_data:
            raise FeatureContractError(
                f"Missing feature: {feature_name}"
            )

        value = category_data[name]

        if not _is_valid_number(value):
            raise FeatureContractError(
                f"Invalid value for {feature_name}: {value}"
            )

        feature_vector.append(float(value))

    return feature_vector


def validate_feature_dict(features):
    """
    Validate nested features and return the flattened ML vector.
    """

    return flatten_feature_dict(features)


def _is_valid_number(value):

    if not isinstance(value, (int, float)):
        return False

    if not math.isfinite(value):
        return False

    if value < 0:
        return False

    return True
