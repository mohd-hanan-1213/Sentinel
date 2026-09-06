import time
import math
from pynput import mouse


class Mouse_collector:

    def __init__(self, event_callback):
        self.event_callback = event_callback

        # Movement state
        self.last_position = None
        self.last_move_time = None

        # Button -> monotonic press timestamp
        self.click_press_times = {}

        self.listener = None

    def on_move(self, x, y):
        # Wall-clock timestamp for the event
        timestamp = time.time()

        # Monotonic timestamp for elapsed-time calculation
        current_time = time.perf_counter()

        # First observed position.
        # This is initialization, not a movement.
        if self.last_position is None:
            self.last_position = (x, y)
            self.last_move_time = current_time
            return

        last_x, last_y = self.last_position

        # Calculate movement distance.
        dist = math.hypot(
            x - last_x,
            y - last_y
        )

        # Calculate elapsed time using monotonic clock.
        time_difference = current_time - self.last_move_time

        # Calculate speed.
        if time_difference > 0:
            speed = dist / time_difference
        else:
            speed = 0.0

        event = {
            "event_type": "mouse_move",
            "timestamp": timestamp,
            "data": {
                "x": x,
                "y": y,
                "distance": dist,
                "speed": speed
            }
        }

        self.event_callback(event)

        # Update movement state.
        self.last_position = (x, y)
        self.last_move_time = current_time

    def on_click(self, x, y, button, pressed):
        timestamp = time.time()
        button_id = str(button)

        if pressed:

            # Use monotonic time for duration measurement.
            press_time = time.perf_counter()

            self.click_press_times[button_id] = press_time

            event = {
                "event_type": "mouse_click_press",
                "timestamp": timestamp,
                "data": {
                    "x": x,
                    "y": y,
                    "button": button_id
                }
            }

            self.event_callback(event)

        else:

            # Retrieve matching press timestamp.
            press_time = self.click_press_times.pop(
                button_id,
                None
            )

            click_duration = None

            if press_time is not None:
                release_time = time.perf_counter()
                click_duration = release_time - press_time

            event = {
                "event_type": "mouse_click_release",
                "timestamp": timestamp,
                "data": {
                    "x": x,
                    "y": y,
                    "button": button_id,
                    "click_duration": click_duration
                }
            }

            self.event_callback(event)

    def on_scroll(self, x, y, dx, dy):
        timestamp = time.time()

        event = {
            "event_type": "mouse_scroll",
            "timestamp": timestamp,
            "data": {
                "x": x,
                "y": y,
                "dx": dx,
                "dy": dy
            }
        }

        self.event_callback(event)

    def start(self):
        self.listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )

        self.listener.start()

    def stop(self):
        if self.listener is not None:
            self.listener.stop()
            self.listener = None


# if __name__ == "__main__":

#     from src.local_agent.buffer.event_buffer import EventBuffer

#     event_buffer = EventBuffer()

#     def handle_event(event):
#         event_buffer.add_event(event)
#         print(event)

#     collector = Mouse_collector(handle_event)

#     collector.start()

#     print(
#         "Mouse collector started. "
#         "Move, click, or scroll. "
#         "Press Ctrl+C to stop."
#     )

#     try:
#         while True:
#             time.sleep(1)

#     except KeyboardInterrupt:
#         collector.stop()

#         print("\nMouse collector stopped.")

#         print(
#             "Events stored in buffer:",
#             event_buffer.size()
#         )
#finished
