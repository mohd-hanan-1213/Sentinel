import os
import sys
import time

from src.local_agent.collector.keyboard_collector import Keyboard_collector
from src.local_agent.collector.mouse_collector import Mouse_collector
from src.local_agent.buffer.event_buffer import EventBuffer
from src.local_agent.features.feature_extractor import FeatureExtractor
from src.local_agent.profile.behavioral_profile import BehavioralProfile
from src.local_agent.integration.pipeline import SentinelPipeline
from src.local_agent.integration.enrollment import EnrollmentManager


SAMPLE_INTERVAL = 30


def is_enrollment_mode():
    return "--enroll" in sys.argv


def main():
    enrollment_mode = is_enrollment_mode()

    event_buffer = EventBuffer()
    feature_extractor = FeatureExtractor()
    behavioral_profile = BehavioralProfile()

    enrollment_manager = None
    pipeline = None
    session_id = None

    if enrollment_mode:
        enrollment_manager = EnrollmentManager()

        print("=" * 60)
        print("SENTINEL BEHAVIORAL ENROLLMENT")
        print("=" * 60)
        print(
            f"Existing enrollment samples: "
            f"{enrollment_manager.sample_count()}/"
            f"{enrollment_manager.required_samples}"
        )
        print()
        print("Enrollment mode collects legitimate-user behavior.")
        print("Use the PC normally while Sentinel is collecting.")
        print("Do not intentionally perform suspicious behavior.")
        print()

        if enrollment_manager.is_ready():
            print("Enrollment is already complete.")
            print("Model:", enrollment_manager.model_file)
            return

    else:
        print("=" * 60)
        print("SENTINEL NORMAL MONITORING")
        print("=" * 60)

        # Normal monitoring requires a trained behavioral model.
        try:
            pipeline = SentinelPipeline()
        except Exception as exc:
            print()
            print("ERROR: Sentinel pipeline could not be initialized.")
            print(f"Reason: {exc}")
            print()
            print(
                "If this is the first setup, complete enrollment first:"
            )
            print()
            print("    python -m src.local_agent.main --enroll")
            print()
            return

        user_id = os.getenv("SENTINEL_USER_ID")

        if user_id:
            try:
                session_id = pipeline.start_session(int(user_id))
                print(f"Session started: {session_id}")
            except Exception as exc:
                print(f"Warning: could not start session: {exc}")
        else:
            print("Warning: SENTINEL_USER_ID is not set.")
            print("ML/Risk/Response processing will still run.")

    def handle_event(event):
        event_buffer.add_event(event)

    keyboard_collector = Keyboard_collector(handle_event)
    mouse_collector = Mouse_collector(handle_event)

    keyboard_collector.start()
    mouse_collector.start()

    print()
    print("Sentinel local agent started.")
    print("Keyboard and mouse collection active.")
    print(f"Feature sampling interval: {SAMPLE_INTERVAL} seconds.")
    print("Press Ctrl+C to stop.")
    print()

    last_sample_time = time.time()

    try:
        while True:
            time.sleep(1)

            current_time = time.time()

            if current_time - last_sample_time >= SAMPLE_INTERVAL:

                events = event_buffer.get_and_clear_events()

                if events:
                    features = feature_extractor.extract(events)

                    behavioral_profile.add_sample(features)

                    print()
                    print("-" * 60)

                    if enrollment_mode:
                        result = enrollment_manager.enroll_sample(
                            features
                        )

                        print("ENROLLMENT SAMPLE")
                        print(
                            f"Accepted: {result['accepted']}"
                        )
                        print(
                            f"Progress: "
                            f"{result['sample_count']}/"
                            f"{result['required_samples']}"
                        )

                        if result["ready"]:
                            print()
                            print("Enrollment complete.")

                            if result["model_trained"]:
                                print(
                                    "Behavioral model trained successfully."
                                )
                                print(
                                    f"Model saved to: "
                                    f"{enrollment_manager.model_file}"
                                )

                            print()
                            print(
                                "You can now start normal monitoring with:"
                            )
                            print(
                                "    python -m src.local_agent.main"
                            )

                            break

                    else:
                        decision = pipeline.process_features(
                            session_id,
                            features
                        )

                        print("--- Security Decision ---")
                        print(decision["response"])

                        print()
                        print("--- ML Output ---")
                        print(decision["ml_output"])

                        print()
                        print("--- Risk Result ---")
                        print(decision["risk"])

                    print()
                    print("--- Behavioral Sample ---")
                    print(features)

                    print()
                    print(
                        "Runtime samples:",
                        behavioral_profile.sample_count()
                    )

                else:
                    print()
                    print("No events collected during interval.")

                last_sample_time = current_time

    except KeyboardInterrupt:
        print()
        print("Stopping Sentinel...")

    finally:
        keyboard_collector.stop()
        mouse_collector.stop()

        print()
        print("=" * 60)

        if enrollment_mode:
            count = enrollment_manager.sample_count()

            print(
                f"Enrollment progress: "
                f"{count}/{enrollment_manager.required_samples}"
            )

            if enrollment_manager.is_ready():
                print("Enrollment complete.")
            else:
                print("Enrollment is incomplete.")
                print(
                    "Run the enrollment command again to continue."
                )

        print(
            "Final runtime samples:",
            behavioral_profile.sample_count()
        )

        print("Sentinel stopped.")
        print("=" * 60)


if __name__ == "__main__":
    main()