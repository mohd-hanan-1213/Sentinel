import json
from pathlib import Path
from typing import List, Sequence

from src.ml.feature_contract import FEATURE_NAMES, validate_feature_vector
from src.ml.profile_builder import MIN_ENROLLMENT_SAMPLES
from src.ml.train_model import train_isolation_forest
from src.ml.model_manager import save_model_bundle


DEFAULT_ENROLLMENT_DIR = Path("models")
DEFAULT_ENROLLMENT_FILE = DEFAULT_ENROLLMENT_DIR / "enrollment_samples.json"
DEFAULT_MODEL_FILE = DEFAULT_ENROLLMENT_DIR / "sentinel_behavior_model.joblib"


class EnrollmentManager:
    """
    Collects legitimate-user behavioral samples and trains
    the Sentinel behavioral authentication model.
    """

    def __init__(
        self,
        enrollment_file: Path = DEFAULT_ENROLLMENT_FILE,
        model_file: Path = DEFAULT_MODEL_FILE,
        required_samples: int = MIN_ENROLLMENT_SAMPLES,
    ):
        self.enrollment_file = Path(enrollment_file)
        self.model_file = Path(model_file)
        self.required_samples = required_samples

    def load_samples(self) -> List[List[float]]:
        """Load previously collected enrollment samples."""
        if not self.enrollment_file.exists():
            return []

        try:
            with self.enrollment_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return []

        if not isinstance(data, list):
            return []

        valid_samples = []

        for sample in data:
            if not isinstance(sample, (list, tuple)):
                continue

            try:
                validate_feature_vector(sample)
            except (ValueError, TypeError):
                continue

            valid_samples.append([float(value) for value in sample])

        return valid_samples

    def add_sample(self, feature_vector: Sequence[float]) -> bool:
        """
        Add one legitimate-user feature vector to enrollment storage.

        Returns True when the sample is accepted.
        """
        try:
            validate_feature_vector(feature_vector)
        except (ValueError, TypeError):
            return False

        samples = self.load_samples()

        if len(samples) >= self.required_samples:
            return False

        samples.append([float(value) for value in feature_vector])

        self.enrollment_file.parent.mkdir(parents=True, exist_ok=True)

        with self.enrollment_file.open("w", encoding="utf-8") as file:
            json.dump(samples, file, indent=2)

        return True

    def sample_count(self) -> int:
        """Return the number of valid enrollment samples."""
        return len(self.load_samples())

    def is_ready(self) -> bool:
        """Return True when enough samples exist to train the model."""
        return self.sample_count() >= self.required_samples

    def train_model(self):
        """
        Train the behavioral model from legitimate enrollment samples.

        Raises RuntimeError if enrollment is incomplete.
        """
        samples = self.load_samples()

        if len(samples) < self.required_samples:
            raise RuntimeError(
                f"Enrollment incomplete: {len(samples)}/"
                f"{self.required_samples} samples collected."
            )

        model_bundle = train_isolation_forest(
            samples,
            min_samples=self.required_samples,
        )

        self.model_file.parent.mkdir(parents=True, exist_ok=True)
        save_model_bundle(model_bundle, self.model_file)

        return model_bundle

    def enroll_sample(self, feature_vector: Sequence[float]):
        """
        Add a sample and automatically train once enrollment is complete.

        Returns:
            dict containing enrollment status.
        """
        accepted = self.add_sample(feature_vector)
        count = self.sample_count()

        result = {
            "accepted": accepted,
            "sample_count": count,
            "required_samples": self.required_samples,
            "ready": count >= self.required_samples,
            "model_trained": False,
        }

        if result["ready"] and not self.model_file.exists():
            self.train_model()
            result["model_trained"] = True

        return result