class FeatureExtractor:

    def extract(self, events):
        """
        Convert raw keyboard and mouse events
        into behavioral features.
        """

        keyboard_features = self._extract_keyboard_features(events)
        mouse_features = self._extract_mouse_features(events)

        return {
            "keyboard": keyboard_features,
            "mouse": mouse_features,
        }

    def _extract_keyboard_features(self, events):

        hold_times = []
        flight_times = []
        pause_durations = []

        for event in events:

            event_type = event.get("event_type")
            data = event.get("data", {})

            if event_type == "keyboard_hold":

                hold_time = data.get("hold_time")

                if self._valid_value(hold_time):
                    hold_times.append(hold_time)

            elif event_type == "keyboard_flight":

                flight_time = data.get("flight_time")

                if self._valid_value(flight_time):
                    flight_times.append(flight_time)

            elif event_type == "keyboard_pause":

                pause_duration = data.get("pause_duration")

                if self._valid_value(pause_duration):
                    pause_durations.append(pause_duration)

        return {
            "average_hold_time": self._average(hold_times),
            "average_flight_time": self._average(flight_times),
            "average_pause_duration": self._average(
                pause_durations
            ),
        }


    def _extract_mouse_features(self, events):

        speeds = []
        distances = []
        click_durations = []

        for event in events:

            event_type = event.get("event_type")
            data = event.get("data", {})

            # Mouse movement
            if event_type == "mouse_move":

                speed = data.get("speed")
                distance = data.get("distance")

                # Only use actual movement.
                if (
                    self._valid_value(speed)
                    and self._valid_value(distance)
                    and distance > 0
                    and speed > 0
                ):
                    speeds.append(speed)
                    distances.append(distance)

            # Mouse click
            elif event_type == "mouse_click_release":

                click_duration = data.get("click_duration")

                if self._valid_value(click_duration):
                    click_durations.append(click_duration)

        return {
            "average_speed": self._average(speeds),
            "average_distance": self._average(distances),
            "average_click_duration": self._average(
                click_durations
            ),
        }

    @staticmethod
    def _average(values):

        if not values:
            return 0.0

        return sum(values) / len(values)

    @staticmethod
    def _valid_value(value):

        if value is None:
            return False

        if not isinstance(value, (int, float)):
            return False

        return value >= 0