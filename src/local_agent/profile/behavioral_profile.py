import math


class BehavioralProfile:

    FEATURE_NAMES = [
        "keyboard.average_hold_time",
        "keyboard.average_flight_time",
        "keyboard.typing_speed",
        "keyboard.average_pause_duration",
        "keyboard.correction_rate",
        "mouse.average_speed",
        "mouse.average_distance",
        "mouse.average_click_duration",
        "mouse.average_acceleration",
        "mouse.direction_changes",
        "mouse.click_rate",
        "mouse.idle_ratio",
    ]

    def __init__(self):
        """
        Store behavioral feature samples.
        """

        self.samples = []

    def add_sample(self, features):

        if not isinstance(features, (list, tuple)):
            return False

        if len(features) != len(self.FEATURE_NAMES):
            return False

        sample = []

        for value in features:

            if self._valid_value(value):
                sample.append(float(value))
            else:
                sample.append(0.0)

        self.samples.append(sample)

        return True

    def sample_count(self):
        """
        Return the number of behavioral samples.
        """

        return len(self.samples)

    def get_baseline(self):

        if not self.samples:
            return None

        feature_count = len(self.FEATURE_NAMES)

        baseline = []

        for i in range(feature_count):

            values = [sample[i] for sample in self.samples]

            baseline.append(sum(values) / len(values))

        return baseline

    def get_statistics(self):

        if not self.samples:
            return None

        statistics = {}

        for i, feature_name in enumerate(self.FEATURE_NAMES):

            values = [sample[i] for sample in self.samples]

            mean = self._mean(values)
            std_dev = self._population_std(values, mean)

            statistics[feature_name] = {
                "mean": mean,
                "std_dev": std_dev,
                "sample_count": len(values),
            }

        return statistics

    def get_samples(self):
        """
        Return all behavioral samples.
        """

        return list(self.samples)

    def get_feature_vector(self, sample_index=-1):
        """
        Return the feature vector for one behavioral sample.

        By default, returns the most recently added sample.
        """

        if not self.samples:
            return None

        return list(self.samples[sample_index])

    def get_sample_vectors(self):
        """
        Return all behavioral sample vectors.
        """

        return [list(sample) for sample in self.samples]

    def get_feature_names(self):

        return list(self.FEATURE_NAMES)

    @staticmethod
    def _get_feature(features, category, feature):

        if isinstance(features, (list, tuple)):

            feature_name = f"{category}.{feature}"

            try:
                feature_index = BehavioralProfile.FEATURE_NAMES.index(feature_name)
            except ValueError:
                return 0.0

            if feature_index >= len(features):
                return 0.0

            value = features[feature_index]

            if value is None:
                return 0.0

            if not isinstance(value, (int, float)):
                return 0.0

            if not math.isfinite(value):
                return 0.0

            if value < 0:
                return 0.0

            return float(value)

        if not isinstance(features, dict):
            return 0.0

        category_data = features.get(category, {})

        if not isinstance(category_data, dict):
            return 0.0

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
    def _valid_value(value):
        """
        Check whether a value is a valid non-negative
        finite number.
        """

        if value is None:
            return False

        if not isinstance(value, (int, float)):
            return False

        if not math.isfinite(value):
            return False

        if value < 0:
            return False

        return True

    @staticmethod
    def _mean(values):
        """
        Calculate arithmetic mean.
        """

        if not values:
            return 0.0

        return sum(values) / len(values)

    @staticmethod
    def _population_std(values, mean):

        if not values:
            return 0.0

        variance = sum((value - mean) ** 2 for value in values) / len(values)

        return math.sqrt(variance)
