from collections import deque

from .thresholds import TEMPORAL_WINDOW_SIZE


class TemporalAnalyzer:
    """
    Maintains recent anomaly scores for a session.

    This class does not decide whether the user is legitimate.
    It only maintains temporal information about recent behaviour.
    """

    def __init__(self, window_size: int = TEMPORAL_WINDOW_SIZE):
        self.window_size = window_size
        self.anomaly_history = deque(maxlen=window_size)

    def update(self, anomaly_score: float) -> None:
        """
        Add a new anomaly score to the temporal history.
        """

        anomaly_score = self._clamp(anomaly_score)
        self.anomaly_history.append(anomaly_score)

    def recent_average(self) -> float:
        """
        Return the average anomaly score in the current
        temporal window.
        """

        if not self.anomaly_history:
            return 0.0

        return sum(self.anomaly_history) / len(self.anomaly_history)

    def get_history(self):
        """
        Return recent anomaly scores.
        """

        return list(self.anomaly_history)

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))


