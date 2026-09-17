from src.local_agent.buffer.event_buffer import EventBuffer
from src.local_agent.collector.keyboard_collector import Keyboard_collector
from src.local_agent.collector.mouse_collector import Mouse_collector
from src.local_agent.features.feature_extractor import FeatureExtractor


class LocalBehaviorPipeline:
    """
    Orchestrate Member 1 data collection and Member 2 feature extraction.
    """

    def __init__(
        self,
        event_buffer=None,
        feature_extractor=None,
        keyboard_collector=None,
        mouse_collector=None,
    ):
        self.event_buffer = event_buffer or EventBuffer()
        self.feature_extractor = feature_extractor or FeatureExtractor()
        self.keyboard_collector = (
            keyboard_collector
            if keyboard_collector is not None
            else Keyboard_collector(self.handle_event)
        )
        self.mouse_collector = (
            mouse_collector
            if mouse_collector is not None
            else Mouse_collector(self.handle_event)
        )
        self.is_running = False

    def handle_event(self, event):
        """
        Receive one raw keyboard/mouse event from Member 1 collectors.
        """

        self.event_buffer.add_event(event)

    def start(self):
        """
        Start keyboard and mouse event collection.
        """

        if self.is_running:
            return

        self.keyboard_collector.start()
        self.mouse_collector.start()
        self.is_running = True

    def stop(self):
        """
        Stop keyboard and mouse event collection.
        """

        self.keyboard_collector.stop()
        self.mouse_collector.stop()
        self.is_running = False

    def collect_feature_window(self):
        """
        Return one flattened Member 2 feature vector for the current window.
        """

        events = self.event_buffer.get_and_clear_events()

        if not events:
            return None

        return self.feature_extractor.extract(events)

    def buffered_event_count(self):
        """
        Return the number of raw events waiting in the current window.
        """

        return self.event_buffer.size()
