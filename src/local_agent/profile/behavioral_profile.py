import math


class BehavioralProfile:

    FEATURE_NAMES = [
        "keyboard.average_hold_time",
        "keyboard.average_flight_time",
        "keyboard.average_pause_duration",
        "mouse.average_speed",
        "mouse.average_distance",
        "mouse.average_click_duration",
    ]

    def __init__(self):
        self.samples = []

    def add_sample(self, features):

        sample = {
            "keyboard": {
                "average_hold_time": self._get_feature(
                    features,
                    "keyboard",
                    "average_hold_time"
                ),
                "average_flight_time": self._get_feature(
                    features,
                    "keyboard",
                    "average_flight_time"
                ),
                "average_pause_duration": self._get_feature(
                    features,
                    "keyboard",
                    "average_pause_duration"
                ),
            },

            "mouse": {
                "average_speed": self._get_feature(
                    features,
                    "mouse",
                    "average_speed"
                ),
                "average_distance": self._get_feature(
                    features,
                    "mouse",
                    "average_distance"
                ),
                "average_click_duration": self._get_feature(
                    features,
                    "mouse",
                    "average_click_duration"
                ),
            }
        }

        self.samples.append(sample)

    def sample_count(self):

        return len(self.samples)

    def get_baseline(self):

        if not self.samples:
            return None

        baseline = {
            "keyboard": {
                "average_hold_time": 0.0,
                "average_flight_time": 0.0,
                "average_pause_duration": 0.0,
            },

            "mouse": {
                "average_speed": 0.0,
                "average_distance": 0.0,
                "average_click_duration": 0.0,
            }
        }

        count = len(self.samples)

        for sample in self.samples:

            for feature in baseline["keyboard"]:
                baseline["keyboard"][feature] += (
                    sample["keyboard"][feature]
                )

            for feature in baseline["mouse"]:
                baseline["mouse"][feature] += (
                    sample["mouse"][feature]
                )

        for category in baseline:

            for feature in baseline[category]:
                baseline[category][feature] /= count

        return baseline

    def get_statistics(self):

        if not self.samples:
            return None

        statistics = {
            "keyboard": {},
            "mouse": {}
        }

        for category in statistics:

            for feature in self.samples[0][category]:

                values = [
                    sample[category][feature]
                    for sample in self.samples
                ]

                mean = self._mean(values)
                std_dev = self._population_std(
                    values,
                    mean
                )

                statistics[category][feature] = {
                    "mean": mean,
                    "std_dev": std_dev
                }

        return statistics

    def get_samples(self):

        return list(self.samples)

    @staticmethod
    def _get_feature(features, category, feature):

        category_data = features.get(category, {})

        value = category_data.get(feature, 0.0)

        if value is None:
            return 0.0

        if not isinstance(value, (int, float)):
            return 0.0

        if not math.isfinite(value):
            return 0.0

        if value < 0:
            return 0.0

        return float(value)

    @staticmethod
    def _mean(values):

        if not values:
            return 0.0

        return sum(values) / len(values)

    @staticmethod
    def _population_std(values, mean):

        if not values:
            return 0.0

        variance = sum(
            (value - mean) ** 2
            for value in values
        ) / len(values)

        return math.sqrt(variance)