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
        """
        Add one behavioral feature vector to the profile.

        Missing or invalid values are converted to 0.0.
        """

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

                "typing_speed": self._get_feature(
                    features,
                    "keyboard",
                    "typing_speed"
                ),

                "average_pause_duration": self._get_feature(
                    features,
                    "keyboard",
                    "average_pause_duration"
                ),

                "correction_rate": self._get_feature(
                    features,
                    "keyboard",
                    "correction_rate"
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

                "average_acceleration": self._get_feature(
                    features,
                    "mouse",
                    "average_acceleration"
                ),

                "direction_changes": self._get_feature(
                    features,
                    "mouse",
                    "direction_changes"
                ),

                "click_rate": self._get_feature(
                    features,
                    "mouse",
                    "click_rate"
                ),

                "idle_ratio": self._get_feature(
                    features,
                    "mouse",
                    "idle_ratio"
                ),
            }
        }

        self.samples.append(sample)

    def sample_count(self):
        """
        Return the number of behavioral samples.
        """

        return len(self.samples)

    def get_baseline(self):
        """
        Return the mean value of every behavioral feature.
        """

        if not self.samples:
            return None

        baseline = {

            "keyboard": {

                "average_hold_time": 0.0,

                "average_flight_time": 0.0,

                "typing_speed": 0.0,

                "average_pause_duration": 0.0,

                "correction_rate": 0.0,
            },

            "mouse": {

                "average_speed": 0.0,

                "average_distance": 0.0,

                "average_click_duration": 0.0,

                "average_acceleration": 0.0,

                "direction_changes": 0.0,

                "click_rate": 0.0,

                "idle_ratio": 0.0,
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
        """

        Returns:

        {
            "keyboard": {
                "feature": {
                    "mean": ...,
                    "std_dev": ...,
                    "sample_count": ...
                }
            },

            "mouse": {
                ...
            }
        }
        """

        if not self.samples:
            return None

        statistics = {
            "keyboard": {},
            "mouse": {}
        }

        for feature in self.samples[0]["keyboard"]:

            values = [
                sample["keyboard"][feature]
                for sample in self.samples
                if self._valid_value(
                    sample["keyboard"][feature]
                )
            ]

            if values:

                mean = self._mean(values)

                std_dev = self._population_std(
                    values,
                    mean
                )

                statistics["keyboard"][feature] = {
                    "mean": mean,
                    "std_dev": std_dev,
                    "sample_count": len(values)
                }

            else:

                statistics["keyboard"][feature] = {
                    "mean": None,
                    "std_dev": None,
                    "sample_count": 0
                }

        for feature in self.samples[0]["mouse"]:

            values = [
                sample["mouse"][feature]
                for sample in self.samples
                if self._valid_value(
                    sample["mouse"][feature]
                )
            ]

            if values:

                mean = self._mean(values)

                std_dev = self._population_std(
                    values,
                    mean
                )

                statistics["mouse"][feature] = {
                    "mean": mean,
                    "std_dev": std_dev,
                    "sample_count": len(values)
                }

            else:

                statistics["mouse"][feature] = {
                    "mean": None,
                    "std_dev": None,
                    "sample_count": 0
                }

        return statistics

    def get_samples(self):
        """
        Return all behavioral samples.
        """

        return list(self.samples)

    def get_feature_vector(self):

        baseline = self.get_baseline()

        if baseline is None:
            return None

        vector = []

        for feature_name in self.FEATURE_NAMES:

            category, feature = feature_name.split(
                ".",
                1
            )

            value = baseline[category][feature]

            if not self._valid_value(value):
                value = 0.0

            vector.append(float(value))

        return vector

    def get_feature_names(self):

        return list(self.FEATURE_NAMES)

    @staticmethod
    def _get_feature(
        features,
        category,
        feature
    ):

        if not isinstance(features, dict):
            return 0.0

        category_data = features.get(
            category,
            {}
        )

        if not isinstance(category_data, dict):
            return 0.0

        value = category_data.get(
            feature,
            0.0
        )

        if value is None:
            return 0.0

        if not isinstance(
            value,
            (int, float)
        ):
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

        if not isinstance(
            value,
            (int, float)
        ):
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
    def _population_std(
        values,
        mean
    ):

        if not values:
            return 0.0

        variance = sum(
            (value - mean) ** 2
            for value in values
        ) / len(values)

        return math.sqrt(variance)