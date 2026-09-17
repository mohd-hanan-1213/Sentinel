from collections import deque
from threading import Lock


class EventBuffer:

    def __init__(self, max_size=10000):
        self.events = deque(maxlen=max_size)
        self.lock = Lock()

    def add_event(self, event):

        with self.lock:
            self.events.append(event)

    def get_all_events(self):

        with self.lock:
            return list(self.events)

    def get_and_clear_events(self):

        with self.lock:
            events = list(self.events)
            self.events.clear()
            return events

    def clear(self):

        with self.lock:
            self.events.clear()

    def size(self):

        with self.lock:
            return len(self.events)