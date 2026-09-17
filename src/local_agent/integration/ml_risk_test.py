from src.ml.mock_data_generator import (
    generate_legitimate_sample,
)
from src.ml.train_model import (
    train_isolation_forest,
)
from src.local_agent.integration.ml_risk_pipeline import (
    MLRiskPipeline,
)


def main():

    print("Testing ML -> Risk integration")
    print("=" * 40)

    # Generate 30 legitimate samples
    # using Member 3's existing mock-data generator.
    training_samples = [
        generate_legitimate_sample()
        for _ in range(30)
    ]

    print("Training samples:", len(training_samples))

    # Train using Member 3's existing ML pipeline.
    model_bundle = train_isolation_forest(
        training_samples
    )

    print("Model type:", model_bundle["model_type"])
    print(
        "Model samples:",
        model_bundle["sample_count"]
    )

    # Give the trained model directly to the bridge.
    # This avoids requiring a saved model file
    # for this integration test.
    pipeline = MLRiskPipeline(
        model_bundle=model_bundle
    )

    # Generate one test behavioural vector.
    feature_vector = generate_legitimate_sample()

    print("\nFeature vector:")
    print(feature_vector)

    # ML -> Risk
    result = pipeline.analyze(
        feature_vector
    )

    print("\nML Output:")
    print(result["ml_output"])

    print("\nRisk Result:")
    print(result["risk_result"])

    print("\nML -> Risk integration test PASSED.")


if __name__ == "__main__":
    main()