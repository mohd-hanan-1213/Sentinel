import time
from pynput import keyboard


class Keyboard_collector:

    def __init__(self, event_callback):
        self.event_callback = event_callback

        self.pressed_keys = {}

        self.last_release_time = None

        # ------------------------------------------------------
        # Maximum gap considered normal typing flight time.
        #
        # <= 0.5 seconds  -> keyboard_flight
        # >  0.5 seconds  -> keyboard_pause
        # ------------------------------------------------------
        self.max_flight_time = 0.5

        self.listener = None


    def on_press(self, key):

        timestamp = time.time()
        key_id = str(key)

        if key_id in self.pressed_keys:
            return

        # Store the timestamp at which the key was pressed.
        self.pressed_keys[key_id] = timestamp

        if self.last_release_time is not None:

            time_gap = timestamp - self.last_release_time

            if 0 <= time_gap <= self.max_flight_time:

                event = {
                    "event_type": "keyboard_flight",
                    "timestamp": timestamp,
                    "data": {
                        "flight_time": time_gap
                    }
                }

            else:

                event = {
                    "event_type": "keyboard_pause",
                    "timestamp": timestamp,
                    "data": {
                        "pause_duration": time_gap
                    }
                }

            self.event_callback(event)

        event = {
            "event_type": "keyboard_press",
            "timestamp": timestamp,
            "data": {}
        }

        self.event_callback(event)


    def on_release(self, key):

        timestamp = time.time()
        key_id = str(key)

        press_time = self.pressed_keys.pop(key_id, None)
        if press_time is None:
            return

        hold_time = timestamp - press_time
        event = {
            "event_type": "keyboard_hold",
            "timestamp": timestamp,
            "data": {
                "hold_time": hold_time
            }
        }

        self.event_callback(event)
        self.last_release_time = timestamp

    def start(self):

        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )

        self.listener.start()

    def stop(self):

        if self.listener is not None:

            self.listener.stop()
            self.listener = None

if __name__ == "__main__":

    def print_event(event):
        print(event)

    collector = Keyboard_collector(print_event)

    collector.start()

    print(
        "Keyboard collector started."
    )
    print(
        "Type normally."
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
            "\nKeyboard collector stopped."
        )