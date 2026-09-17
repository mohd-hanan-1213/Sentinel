import os
import time

from src.local_agent.integration.pipeline import SentinelPipeline
from src.local_agent.local_behavior_pipeline import LocalBehaviorPipeline


DEFAULT_SAMPLE_INTERVAL = 15
DEFAULT_USER_ID = 1


def main():
    sample_interval = int(
        os.getenv("SENTINEL_SAMPLE_INTERVAL", DEFAULT_SAMPLE_INTERVAL)
    )
    user_id = int(os.getenv("SENTINEL_USER_ID", DEFAULT_USER_ID))

    local_behavior_pipeline = LocalBehaviorPipeline()
    sentinel_pipeline = SentinelPipeline()
    session_id = sentinel_pipeline.start_session(user_id=user_id)

    local_behavior_pipeline.start()

    print("Sentinel runtime started.")
    print("Member 1 + 2 local behaviour pipeline active.")
    print("Member 3 authentication pipeline connected.")
    print("Member 4 risk/response pipeline connected.")
    print(f"Session ID: {session_id}")
    print(f"Feature sampling interval: {sample_interval} seconds.")
    print("Press Ctrl+C to stop.")

    last_sample_time = time.time()

    try:
        while True:
            time.sleep(1)

            current_time = time.time()

            if current_time - last_sample_time < sample_interval:
                continue

            feature_vector = (
                local_behavior_pipeline.collect_feature_window()
            )

            if feature_vector is None:
                print("\nNo events collected during interval.")
                last_sample_time = current_time
                continue

            result = sentinel_pipeline.process_features(
                session_id,
                feature_vector,
            )

            print("\n--- Sentinel Pipeline Result ---")
            print(result)

            last_sample_time = current_time

    except KeyboardInterrupt:
        print("\nStopping Sentinel runtime...")

    finally:
        local_behavior_pipeline.stop()

        print("Local behaviour pipeline stopped.")
        print("\n==============================")
        print("Sentinel stopped.")
        print("==============================")


if __name__ == "__main__":
    main()
