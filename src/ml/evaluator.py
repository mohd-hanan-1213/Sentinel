from src.ml.anomaly_detector import detect_anomaly
from src.ml.mock_data_generator import (
    ATTACKER_LABEL,
    LEGITIMATE_LABEL,
    generate_dataset,
    generate_legitimate_sample,
)
from src.ml.train_model import train_isolation_forest


DEFAULT_TRAIN_COUNT = 30
DEFAULT_TEST_LEGITIMATE_COUNT = 30
DEFAULT_TEST_ATTACKER_COUNT = 30


def evaluate_model(
    train_count=DEFAULT_TRAIN_COUNT,
    test_legitimate_count=DEFAULT_TEST_LEGITIMATE_COUNT,
    test_attacker_count=DEFAULT_TEST_ATTACKER_COUNT,
):
    """
    Train on mock legitimate samples and evaluate on mock test data.
    """

    training_samples = [
        generate_legitimate_sample()
        for _ in range(train_count)
    ]

    model_bundle = train_isolation_forest(training_samples)

    test_samples, true_labels = generate_dataset(
        test_legitimate_count,
        test_attacker_count,
    )

    predicted_labels = [
        _predict_label(sample, model_bundle)
        for sample in test_samples
    ]

    return _calculate_metrics(
        true_labels,
        predicted_labels,
        train_count,
        test_legitimate_count,
        test_attacker_count,
    )


def print_metrics(metrics):
    """
    Print a readable evaluation report.
    """

    print("Sentinel ML Evaluation")
    print("======================")
    print(f"Training samples: {metrics['train_count']}")
    print(f"Total test samples: {metrics['total_samples']}")
    print(f"Legitimate test samples: {metrics['total_legitimate']}")
    print(f"Attacker test samples: {metrics['total_attackers']}")
    print()
    print("Metrics")
    print("-------")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1-score: {metrics['f1_score']:.4f}")
    print(
        "False acceptance rate: "
        f"{metrics['false_acceptance_rate']:.4f}"
    )
    print(
        "False rejection rate: "
        f"{metrics['false_rejection_rate']:.4f}"
    )
    print()
    print("Confusion Counts")
    print("----------------")
    print(f"True positives: {metrics['true_positives']}")
    print(f"True negatives: {metrics['true_negatives']}")
    print(f"False positives: {metrics['false_positives']}")
    print(f"False negatives: {metrics['false_negatives']}")


def main():
    """
    Run the mock-data evaluator from the command line.
    """

    metrics = evaluate_model()
    print_metrics(metrics)


def _predict_label(sample, model_bundle):

    result = detect_anomaly(
        sample,
        model_bundle=model_bundle,
    )

    if result["is_deviation"]:
        return ATTACKER_LABEL

    return LEGITIMATE_LABEL


def _calculate_metrics(
    true_labels,
    predicted_labels,
    train_count,
    total_legitimate,
    total_attackers,
):

    true_positives = 0
    true_negatives = 0
    false_positives = 0
    false_negatives = 0

    for true_label, predicted_label in zip(
        true_labels,
        predicted_labels,
    ):

        if (
            true_label == ATTACKER_LABEL
            and predicted_label == ATTACKER_LABEL
        ):
            true_positives += 1
        elif (
            true_label == LEGITIMATE_LABEL
            and predicted_label == LEGITIMATE_LABEL
        ):
            true_negatives += 1
        elif (
            true_label == LEGITIMATE_LABEL
            and predicted_label == ATTACKER_LABEL
        ):
            false_positives += 1
        elif (
            true_label == ATTACKER_LABEL
            and predicted_label == LEGITIMATE_LABEL
        ):
            false_negatives += 1

    total_samples = len(true_labels)

    accuracy = _safe_divide(
        true_positives + true_negatives,
        total_samples,
    )

    precision = _safe_divide(
        true_positives,
        true_positives + false_positives,
    )

    recall = _safe_divide(
        true_positives,
        true_positives + false_negatives,
    )

    f1_score = _safe_divide(
        2 * precision * recall,
        precision + recall,
    )

    false_acceptance_rate = _safe_divide(
        false_negatives,
        total_attackers,
    )

    false_rejection_rate = _safe_divide(
        false_positives,
        total_legitimate,
    )

    return {
        "train_count": train_count,
        "total_samples": total_samples,
        "total_legitimate": total_legitimate,
        "total_attackers": total_attackers,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "false_acceptance_rate": false_acceptance_rate,
        "false_rejection_rate": false_rejection_rate,
        "true_positives": true_positives,
        "true_negatives": true_negatives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def _safe_divide(numerator, denominator):

    if denominator == 0:
        return 0.0

    return numerator / denominator


if __name__ == "__main__":
    main()
