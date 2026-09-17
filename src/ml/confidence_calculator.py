RAW_SCORE_SCALE = 2.0


def calculate_confidence_scores(
    raw_score,
    score_scale=RAW_SCORE_SCALE,
):
    """
    Convert an Isolation Forest raw score into bounded scores.

    Higher raw scores are more normal. Lower raw scores are more
    anomalous. This v1 conversion is intentionally simple and can
    be calibrated later with real evaluation data.
    """

    if score_scale <= 0:
        raise ValueError(
            "Score scale must be positive."
        )

    anomaly_score = 0.5 - (float(raw_score) * score_scale)
    anomaly_score = _clamp(anomaly_score)

    legitimate_confidence = 1.0 - anomaly_score

    return {
        "anomaly_score": anomaly_score,
        "legitimate_confidence": legitimate_confidence,
    }


def _clamp(value):

    return min(
        max(float(value), 0.0),
        1.0,
    )
