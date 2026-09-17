import random

from src.ml.feature_contract import (
    FEATURE_NAMES,
    validate_feature_vector,
)


LEGITIMATE_LABEL = 0
ATTACKER_LABEL = 1


LEGITIMATE_PROFILE = {
    "keyboard.average_hold_time": 0.12,
    "keyboard.average_flight_time": 0.09,
    "keyboard.typing_speed": 4.8,
    "keyboard.average_pause_duration": 0.35,
    "keyboard.correction_rate": 0.04,
    "mouse.average_speed": 320.0,
    "mouse.average_distance": 42.0,
    "mouse.average_click_duration": 0.11,
    "mouse.average_acceleration": 52.0,
    "mouse.direction_changes": 2.1,
    "mouse.click_rate": 0.15,
    "mouse.idle_ratio": 0.18,
}


LEGITIMATE_VARIATION = {
    "keyboard.average_hold_time": 0.025,
    "keyboard.average_flight_time": 0.02,
    "keyboard.typing_speed": 0.45,
    "keyboard.average_pause_duration": 0.08,
    "keyboard.correction_rate": 0.02,
    "mouse.average_speed": 45.0,
    "mouse.average_distance": 8.0,
    "mouse.average_click_duration": 0.025,
    "mouse.average_acceleration": 12.0,
    "mouse.direction_changes": 0.55,
    "mouse.click_rate": 0.04,
    "mouse.idle_ratio": 0.06,
}


ATTACKER_PROFILE = {
    "keyboard.average_hold_time": 0.19,
    "keyboard.average_flight_time": 0.15,
    "keyboard.typing_speed": 3.2,
    "keyboard.average_pause_duration": 0.62,
    "keyboard.correction_rate": 0.11,
    "mouse.average_speed": 470.0,
    "mouse.average_distance": 67.0,
    "mouse.average_click_duration": 0.18,
    "mouse.average_acceleration": 88.0,
    "mouse.direction_changes": 4.2,
    "mouse.click_rate": 0.28,
    "mouse.idle_ratio": 0.32,
}


ATTACKER_VARIATION = {
    "keyboard.average_hold_time": 0.04,
    "keyboard.average_flight_time": 0.035,
    "keyboard.typing_speed": 0.75,
    "keyboard.average_pause_duration": 0.13,
    "keyboard.correction_rate": 0.04,
    "mouse.average_speed": 80.0,
    "mouse.average_distance": 14.0,
    "mouse.average_click_duration": 0.04,
    "mouse.average_acceleration": 20.0,
    "mouse.direction_changes": 0.9,
    "mouse.click_rate": 0.07,
    "mouse.idle_ratio": 0.1,
}


def generate_legitimate_sample():
    """
    Return one normal-user feature vector.
    """

    return _generate_sample(
        LEGITIMATE_PROFILE,
        LEGITIMATE_VARIATION,
    )


def generate_attacker_sample():
    """
    Return one different-user/anomalous feature vector.
    """

    return _generate_sample(
        ATTACKER_PROFILE,
        ATTACKER_VARIATION,
    )


def generate_dataset(
    legitimate_count,
    attacker_count,
    shuffle=True,
):
    """
    Return mock feature vectors and labels for evaluation.

    Labels:
        0 = legitimate
        1 = attacker/anomalous
    """

    if legitimate_count < 0 or attacker_count < 0:
        raise ValueError(
            "Sample counts must be non-negative."
        )

    samples = []
    labels = []

    for _ in range(legitimate_count):
        samples.append(generate_legitimate_sample())
        labels.append(LEGITIMATE_LABEL)

    for _ in range(attacker_count):
        samples.append(generate_attacker_sample())
        labels.append(ATTACKER_LABEL)

    if shuffle:
        combined = list(zip(samples, labels))
        random.shuffle(combined)

        if combined:
            samples, labels = zip(*combined)
            samples = list(samples)
            labels = list(labels)
        else:
            samples = []
            labels = []

    return samples, labels


def _generate_sample(profile, variation):

    sample = []

    for feature_name in FEATURE_NAMES:
        center = profile[feature_name]
        spread = variation[feature_name]
        value = random.gauss(center, spread)
        sample.append(max(value, 0.0))

    return validate_feature_vector(sample)
