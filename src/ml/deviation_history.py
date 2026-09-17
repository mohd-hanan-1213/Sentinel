DEFAULT_HISTORY_SIZE = 5
DEFAULT_DEVIATION_THRESHOLD = 0.6


class DeviationHistory:
    """
    Track recent anomaly results across behavioural windows.
    """

    def __init__(
        self,
        history_size=DEFAULT_HISTORY_SIZE,
        deviation_threshold=DEFAULT_DEVIATION_THRESHOLD,
    ):

        if history_size <= 0:
            raise ValueError(
                "History size must be positive."
            )

        if not 0.0 <= deviation_threshold <= 1.0:
            raise ValueError(
                "Deviation threshold must be between 0.0 and 1.0."
            )

        self.history_size = history_size
        self.deviation_threshold = deviation_threshold
        self._results = []

    def add_result(self, anomaly_result):
        """
        Store one per-window anomaly result.
        """

        validated_result = self._validate_result(
            anomaly_result
        )

        self._results.append(validated_result)
        self._results = self._results[-self.history_size:]

        return validated_result

    def get_recent_results(self):
        """
        Return a copy of stored recent anomaly results.
        """

        return [
            dict(result)
            for result in self._results
        ]

    def get_recent_anomaly_average(self):
        """
        Return the average anomaly score for stored windows.
        """

        if not self._results:
            return 0.0

        total = sum(
            result["anomaly_score"]
            for result in self._results
        )

        return total / len(self._results)

    def get_consecutive_deviation_count(self):
        """
        Count latest consecutive deviating windows.
        """

        count = 0

        for result in reversed(self._results):
            if self._is_deviation(result):
                count += 1
            else:
                break

        return count

    def has_repeated_deviation(self, min_consecutive=3):
        """
        Return True when enough recent windows deviate in a row.
        """

        if min_consecutive <= 0:
            raise ValueError(
                "Minimum consecutive count must be positive."
            )

        return (
            self.get_consecutive_deviation_count()
            >= min_consecutive
        )

    def build_summary(self):
        """
        Return a compact recent-deviation summary.
        """

        latest_result = (
            self._results[-1]
            if self._results
            else None
        )

        return {
            "history_size": self.history_size,
            "window_count": len(self._results),
            "recent_anomaly_average": (
                self.get_recent_anomaly_average()
            ),
            "consecutive_deviation_count": (
                self.get_consecutive_deviation_count()
            ),
            "has_repeated_deviation": (
                self.has_repeated_deviation()
            ),
            "latest_anomaly_score": (
                latest_result["anomaly_score"]
                if latest_result
                else None
            ),
            "latest_confidence": (
                latest_result["legitimate_confidence"]
                if latest_result
                else None
            ),
        }

    def _is_deviation(self, anomaly_result):

        return (
            anomaly_result["is_deviation"]
            or anomaly_result["anomaly_score"]
            >= self.deviation_threshold
        )

    @staticmethod
    def _validate_result(anomaly_result):

        if not isinstance(anomaly_result, dict):
            raise ValueError(
                "Anomaly result must be a dictionary."
            )

        required_keys = [
            "anomaly_score",
            "legitimate_confidence",
            "is_deviation",
        ]

        missing_keys = [
            key
            for key in required_keys
            if key not in anomaly_result
        ]

        if missing_keys:
            raise ValueError(
                "Anomaly result is missing required keys: "
                + ", ".join(missing_keys)
            )

        anomaly_score = anomaly_result["anomaly_score"]
        legitimate_confidence = (
            anomaly_result["legitimate_confidence"]
        )

        if not 0.0 <= anomaly_score <= 1.0:
            raise ValueError(
                "Anomaly score must be between 0.0 and 1.0."
            )

        if not 0.0 <= legitimate_confidence <= 1.0:
            raise ValueError(
                "Legitimate confidence must be between 0.0 and 1.0."
            )

        if not isinstance(anomaly_result["is_deviation"], bool):
            raise ValueError(
                "is_deviation must be a boolean."
            )

        return dict(anomaly_result)
