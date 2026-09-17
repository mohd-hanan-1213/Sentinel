# Risk score boundaries
LOW_THRESHOLD = 30
MEDIUM_THRESHOLD = 60
HIGH_THRESHOLD = 81


# Risk calculation weights
ANOMALY_WEIGHT = 0.45
RECENT_ANOMALY_WEIGHT = 0.25
CONFIDENCE_WEIGHT = 0.15
PERSISTENCE_WEIGHT = 0.15


# Maximum number of consecutive deviations
MAX_CONSECUTIVE_DEVIATIONS = 5


# Number of recent anomaly values used for temporal analysis
TEMPORAL_WINDOW_SIZE = 5