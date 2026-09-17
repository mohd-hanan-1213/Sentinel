import time

from src.local_agent.collector.keyboard_collector import Keyboard_collector
from src.local_agent.collector.mouse_collector import Mouse_collector
from src.local_agent.buffer.event_buffer import EventBuffer
from src.local_agent.features.feature_extractor import FeatureExtractor
from src.ml.authentication_pipeline import AuthenticationPipeline

SAMPLE_INTERVAL = 15


def main():

    event_buffer = EventBuffer()
    feature_extractor = FeatureExtractor()
    authentication_pipeline = AuthenticationPipeline()

    def handle_event(event):
        event_buffer.add_event(event)

    keyboard_collector = Keyboard_collector(handle_event)
    mouse_collector = Mouse_collector(handle_event)

    keyboard_collector.start()
    mouse_collector.start()

    print("Sentinel local agent started.")
    print("Keyboard and mouse collection active.")
    print(f"Feature sampling interval: " f"{SAMPLE_INTERVAL} seconds.")
    print("Press Ctrl+C to stop.")

    last_sample_time = time.time()

    try:

        while True:

            time.sleep(1)

            current_time = time.time()

            if current_time - last_sample_time >= SAMPLE_INTERVAL:

                # Get events for this sampling interval
                events = event_buffer.get_and_clear_events()

                if events:

                    feature_vector = feature_extractor.extract(events)

                    # --------------------------------------------------
                    # Process feature vector through Member 3 ML pipeline
                    # --------------------------------------------------

                    result = authentication_pipeline.process_feature_vector(
                        feature_vector
                    )

                    print("\n--- Behavioral Feature Vector ---")
                    print(feature_vector)

                    print("\n--- Member 3 Result ---")
                    print(result)

                    print(
                        "Pipeline mode:",
                        authentication_pipeline.get_mode()
                    )

                else:

                    print("\nNo events collected " "during interval.")

                last_sample_time = current_time

    except KeyboardInterrupt:

        print("\nStopping Sentinel local agent...")

    finally:

        keyboard_collector.stop()
        mouse_collector.stop()

        print("Keyboard collector stopped.")
        print("Mouse collector stopped.")
        print("\n==============================")
        print("Sentinel stopped.")
        print("==============================")

        print(
            "Final pipeline mode:",
            authentication_pipeline.get_mode()
        )


if __name__ == "__main__":
    main()
