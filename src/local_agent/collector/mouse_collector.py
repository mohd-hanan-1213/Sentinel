import time
import math
import pyautogui
from pynput import mouse


class Mouse_collector:

    def __init__(self, event_callback):
        self.event_callback = event_callback

        self.screen_width, self.screen_height = (
            pyautogui.size()
        )

        # Prevent division by zero.
        if self.screen_width <= 0:
            self.screen_width = 1

        if self.screen_height <= 0:
            self.screen_height = 1

        self.last_position = None
        self.last_moveTime = None

        # Button -> press timestamp
        self.click_press_times = {}

        self.listener = None
    def _normalize_position(self, x, y):
        """
        Convert screen coordinates into normalized coordinates.

        x: 0 -> screen_width
        y: 0 -> screen_height

        normalized x/y:
        0.0 -> 1.0
        """

        normalized_x = x / self.screen_width
        normalized_y = y / self.screen_height

        # Keep values inside [0, 1].
        normalized_x = min(
            max(normalized_x, 0.0),
            1.0
        )

        normalized_y = min(
            max(normalized_y, 0.0),
            1.0
        )

        return normalized_x, normalized_y

    def on_move(self, x, y):

        timestamp = time.time()

        normalized_x, normalized_y = (
            self._normalize_position(x, y)
        )

        if self.last_position is None:

            self.last_position = (
                normalized_x,
                normalized_y
            )

            self.last_moveTime = timestamp

            return

        last_x, last_y = self.last_position

        dist = math.hypot(
            normalized_x - last_x,
            normalized_y - last_y
        )

        time_difference = (
            timestamp - self.last_moveTime
        )

        if time_difference > 0:

            speed = (
                dist / time_difference
            )

        else:

            speed = 0.0

        event = {
            "event_type": "mouse_move",
            "timestamp": timestamp,
            "data": {
                # Normalized coordinates
                "x": normalized_x,
                "y": normalized_y,

                # Normalized distance
                "distance": dist,

                # Normalized distance / second
                "speed": speed
            }
        }

        self.event_callback(event)

        self.last_position = (
            normalized_x,
            normalized_y
        )

        self.last_moveTime = timestamp

    def on_click(self, x, y, button, pressed):

        timestamp = time.time()
        button_id = str(button)

        normalized_x, normalized_y = (
            self._normalize_position(x, y)
        )

        if pressed:

            # Store exact press timestamp.
            self.click_press_times[button_id] = timestamp

            event = {
                "event_type": "mouse_click_press",
                "timestamp": timestamp,
                "data": {
                    "x": normalized_x,
                    "y": normalized_y,
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

                click_duration = (
                    timestamp - press_time
                )

            event = {
                "event_type": "mouse_click_release",
                "timestamp": timestamp,
                "data": {
                    "x": normalized_x,
                    "y": normalized_y,
                    "button": button_id,
                    "click_duration": click_duration
                }
            }

            self.event_callback(event)

    def on_scroll(self, x, y, dx, dy):

        timestamp = time.time()

        normalized_x, normalized_y = (
            self._normalize_position(x, y)
        )

        event = {
            "event_type": "mouse_scroll",
            "timestamp": timestamp,
            "data": {
                "x": normalized_x,
                "y": normalized_y,
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


if __name__ == "__main__":

    def print_event(event):
        print(event)

    collector = Mouse_collector(print_event)

    print(
        "Screen size:",
        collector.screen_width,
        "x",
        collector.screen_height
    )

    collector.start()

    print(
        "Mouse collector started."
    )

    print(
        "Move, click, or scroll."
    )

    print(
        "Press Ctrl+C to stop."
    )

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        collector.stop()

        print(
            "\nMouse collector stopped."
        )