from src.ml.feature_contract import (
    FEATURE_COUNT,
    FEATURE_NAMES,
    validate_feature_vector,
)


MIN_ENROLLMENT_SAMPLES = 30


class ProfileBuilder:
    """
    Build a legitimate-user enrolment profile from validated
    behavioural feature vectors.
    """

    def __init__(
        self,
        min_enrollment_samples=MIN_ENROLLMENT_SAMPLES,
    ):

        if min_enrollment_samples <= 0:
            raise ValueError(
                "Minimum enrollment samples must be positive."
            )

        self.min_enrollment_samples = min_enrollment_samples
        self._samples = []

    def add_sample(self, feature_vector):
        """
        Validate and store one legitimate-user feature vector.
        """

        validated_vector = validate_feature_vector(
            feature_vector
        )

        self._samples.append(validated_vector)

        return validated_vector

    def add_samples(self, feature_vectors):
        """
        Validate and store multiple legitimate-user feature vectors.
        """

        for feature_vector in feature_vectors:
            self.add_sample(feature_vector)

        return self.sample_count()

    def sample_count(self):
        """
        Return the number of enrolment samples stored.
        """

        return len(self._samples)

    def is_ready(self):
        """
        Return True when enough samples exist for enrolment.
        """

        return (
            self.sample_count()
            >= self.min_enrollment_samples
        )

    def get_samples(self):
        """
        Return a copy of the validated enrolment samples.
        """

        return [
            list(sample)
            for sample in self._samples
        ]

    def get_feature_names(self):
        """
        Return the fixed ML feature order.
        """

        return list(FEATURE_NAMES)

    def build_profile(self):
        """
        Return enrolment metadata and per-feature statistics.
        """

        return {
            "sample_count": self.sample_count(),
            "is_ready": self.is_ready(),
            "feature_names": self.get_feature_names(),
            "statistics": self._build_statistics(),
        }

    def _build_statistics(self):

        statistics = {}

        for index, feature_name in enumerate(FEATURE_NAMES):
            values = [
                sample[index]
                for sample in self._samples
            ]

            statistics[feature_name] = (
                self._calculate_statistics(values)
            )

        return statistics

    @staticmethod
    def _calculate_statistics(values):

        if not values:
            return {
                "mean": None,
                "min": None,
                "max": None,
            }

        return {
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }


def build_profile_from_samples(
    feature_vectors,
    min_enrollment_samples=MIN_ENROLLMENT_SAMPLES,
):
    """
    Convenience helper for building a profile from existing samples.
    """

    profile_builder = ProfileBuilder(
        min_enrollment_samples=min_enrollment_samples
    )

    profile_builder.add_samples(feature_vectors)

    return profile_builder.build_profile()
