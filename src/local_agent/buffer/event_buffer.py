from collections import deque
from threading import Lock

class EventBuffer:
    def __init__(self,max_size=10000):
        self.events=deque(maxlen=max_size)
        self.lock=Lock()

    def add_event(self,event):
        with self.lock:
            self.events.append(event)

    def get_events(self):
        with self.lock:
            return list(self.events)

    def cleat(self):
        with self.lock:
            self.events.clear()

    def size(self):
        with self.lock:
            return len(self.events)


if __name__ == "__main__":
    buffer = EventBuffer(max_size=5)

    buffer.add_event({
        "event_type": "keyboard_press",
        "timestamp": 123456.0,
        "data": {}
    })

    buffer.add_event({
        "event_type": "mouse_move",
        "timestamp": 123457.0,
        "data": {
            "x": 100,
            "y": 200
        }
    })

    print("Buffer size:", buffer.size())
    print("Events:")
    print(buffer.get_events())