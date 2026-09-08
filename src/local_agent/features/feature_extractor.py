import math


class FeatureExtractor:

    # Movement below this distance is treated as insignificant
    # when calculating direction changes.
    MIN_MOVEMENT_DISTANCE = 1.0

    # A mouse movement gap greater than this is considered idle.
    IDLE_THRESHOLD = 1.0

    def extract(self, events):
        """

        Returns:
            {
                "keyboard": {
                    ...
                },
                "mouse": {
                    ...
                }
            }
        """

        if not isinstance(events, list):
            events = list(events) if events else []

        events = self._preprocess_events(events)

        keyboard_features = self._extract_keyboard_features(events)
        mouse_features = self._extract_mouse_features(events)

        return {
            "keyboard": keyboard_features,
            "mouse": mouse_features,
        }

    def _preprocess_events(self, events):
        """
        Remove malformed events and sort them by timestamp.
        """

        cleaned_events = []

        for event in events:

            if not isinstance(event, dict):
                continue

            event_type = event.get("event_type")
            timestamp = event.get("timestamp")
            data = event.get("data", {})

            if not isinstance(event_type, str):
                continue

            if not self._valid_value(timestamp):
                continue

            if not isinstance(data, dict):
                continue

            cleaned_events.append(event)

        cleaned_events.sort(
            key=lambda event: event["timestamp"]
        )

        return cleaned_events

    def _extract_keyboard_features(self, events):

        hold_times = []
        flight_times = []
        pause_durations = []

        keyboard_activity_times = []

        correction_count = 0
        keyboard_action_count = 0

        for event in events:

            event_type = event.get("event_type")
            data = event.get("data", {})
            timestamp = event.get("timestamp")

            if event_type == "keyboard_hold":

                hold_time = data.get("hold_time")

                if self._valid_value(hold_time):

                    hold_times.append(float(hold_time))
                    keyboard_activity_times.append(timestamp)

            elif event_type == "keyboard_flight":

                flight_time = data.get("flight_time")

                if self._valid_value(flight_time):

                    flight_times.append(float(flight_time))
                    keyboard_activity_times.append(timestamp)

            elif event_type == "keyboard_pause":

                pause_duration = data.get("pause_duration")

                if self._valid_value(pause_duration):

                    pause_durations.append(
                        float(pause_duration)
                    )

                    keyboard_activity_times.append(timestamp)

            elif event_type == "keyboard_press":

                keyboard_action_count += 1
                keyboard_activity_times.append(timestamp)

                #
                # data = {
                #     "key": "Key.space"
                # }
                #
                # We don't store the actual typed content.
                key = data.get("key")

                if isinstance(key, str):

                    key_lower = key.lower()

                    if (
                        "backspace" in key_lower
                        or "delete" in key_lower
                    ):
                        correction_count += 1

        typing_speed = self._calculate_typing_speed(
            keyboard_activity_times,
            keyboard_action_count
        )

        correction_rate = self._calculate_correction_rate(
            correction_count,
            keyboard_action_count
        )

        return {
            "average_hold_time": self._average(
                hold_times
            ),

            "average_flight_time": self._average(
                flight_times
            ),

            "typing_speed": typing_speed,

            "average_pause_duration": self._average(
                pause_durations
            ),

            "correction_rate": correction_rate,
        }

    def _calculate_typing_speed(
        self,
        timestamps,
        key_count
    ):

        if key_count <= 0:
            return 0.0

        if len(timestamps) < 2:
            return 0.0

        start_time = min(timestamps)
        end_time = max(timestamps)

        duration = end_time - start_time

        if duration <= 0:
            return 0.0

        return key_count / duration

    def _calculate_correction_rate(
        self,
        correction_count,
        keyboard_action_count
    ):

        if keyboard_action_count <= 0:
            return 0.0

        return correction_count / keyboard_action_count

    def _extract_mouse_features(self, events):

        speeds = []
        distances = []
        click_durations = []

        movement_records = []

        direction_vectors = []

        click_timestamps = []

        mouse_activity_timestamps = []

        for event in events:

            event_type = event.get("event_type")
            data = event.get("data", {})
            timestamp = event.get("timestamp")

            if event_type == "mouse_move":

                speed = data.get("speed")
                distance = data.get("distance")

                x = data.get("x")
                y = data.get("y")

                if (
                    self._valid_value(speed)
                    and self._valid_value(distance)
                    and distance > 0
                    and speed >= 0
                ):

                    speed = float(speed)
                    distance = float(distance)

                    speeds.append(speed)
                    distances.append(distance)

                    movement_records.append({
                        "timestamp": float(timestamp),
                        "speed": speed,
                        "distance": distance,
                        "x": x,
                        "y": y
                    })

                    mouse_activity_timestamps.append(
                        float(timestamp)
                    )

                    if (
                        self._valid_value(x)
                        and self._valid_value(y)
                    ):

                        direction_vectors.append(
                            (
                                float(x),
                                float(y),
                                distance
                            )
                        )

            elif event_type == "mouse_click_release":

                click_duration = data.get(
                    "click_duration"
                )

                if self._valid_value(click_duration):

                    click_durations.append(
                        float(click_duration)
                    )

                click_timestamps.append(
                    float(timestamp)
                )

                mouse_activity_timestamps.append(
                    float(timestamp)
                )

            elif event_type == "mouse_click_press":

                click_timestamps.append(
                    float(timestamp)
                )

                mouse_activity_timestamps.append(
                    float(timestamp)
                )

            elif event_type == "mouse_scroll":

                mouse_activity_timestamps.append(
                    float(timestamp)
                )

        average_acceleration = (
            self._calculate_average_acceleration(
                movement_records
            )
        )

        direction_changes = (
            self._calculate_direction_changes(
                direction_vectors
            )
        )

        click_rate = self._calculate_click_rate(
            click_timestamps
        )

        idle_ratio = self._calculate_idle_ratio(
            events
        )

        return {
            "average_speed": self._average(
                speeds
            ),

            "average_distance": self._average(
                distances
            ),

            "average_click_duration": self._average(
                click_durations
            ),

            "average_acceleration": average_acceleration,

            "direction_changes": direction_changes,

            "click_rate": click_rate,

            "idle_ratio": idle_ratio,
        }

    def _calculate_average_acceleration(
        self,
        movement_records
    ):
        """

        acceleration =
            change in speed / change in time
        """

        if len(movement_records) < 2:
            return 0.0

        accelerations = []

        previous = movement_records[0]

        for current in movement_records[1:]:

            time_difference = (
                current["timestamp"]
                - previous["timestamp"]
            )

            if time_difference <= 0:
                previous = current
                continue

            speed_difference = (
                current["speed"]
                - previous["speed"]
            )

            acceleration = (
                abs(speed_difference)
                / time_difference
            )

            if math.isfinite(acceleration):

                accelerations.append(
                    acceleration
                )

            previous = current

        return self._average(accelerations)

    def _calculate_direction_changes(
        self,
        direction_vectors
    ):

        if len(direction_vectors) < 3:
            return 0

        # Convert positions into movement vectors.
        vectors = []

        previous_x, previous_y, _ = direction_vectors[0]

        for x, y, distance in direction_vectors[1:]:

            dx = x - previous_x
            dy = y - previous_y

            movement_distance = math.hypot(
                dx,
                dy
            )

            if (
                movement_distance
                >= self.MIN_MOVEMENT_DISTANCE
            ):

                vectors.append(
                    (dx, dy)
                )

            previous_x = x
            previous_y = y

        if len(vectors) < 2:
            return 0

        direction_changes = 0

        previous_dx, previous_dy = vectors[0]

        for dx, dy in vectors[1:]:

            previous_angle = math.atan2(
                previous_dy,
                previous_dx
            )

            current_angle = math.atan2(
                dy,
                dx
            )

            angle_difference = abs(
                current_angle
                - previous_angle
            )

            # Normalize angle difference to [0, pi].
            if angle_difference > math.pi:
                angle_difference = (
                    2 * math.pi
                    - angle_difference
                )

            # A change greater than 45 degrees
            # is treated as a direction change.
            if angle_difference >= math.pi / 4:
                direction_changes += 1

            previous_dx = dx
            previous_dy = dy

        return direction_changes

    def _calculate_click_rate(
        self,
        click_timestamps
    ):

        if not click_timestamps:
            return 0.0

        if len(click_timestamps) == 1:
            return 0.0

        start_time = min(click_timestamps)
        end_time = max(click_timestamps)

        duration = end_time - start_time

        if duration <= 0:
            return 0.0

        return len(click_timestamps) / duration

    # =========================================================
    # IDLE RATIO
    # =========================================================

    def _calculate_idle_ratio(self, events):

        if len(events) < 2:
            return 0.0

        timestamps = []

        for event in events:

            timestamp = event.get("timestamp")

            if self._valid_value(timestamp):

                timestamps.append(
                    float(timestamp)
                )

        if len(timestamps) < 2:
            return 0.0

        timestamps.sort()

        total_duration = (
            timestamps[-1]
            - timestamps[0]
        )

        if total_duration <= 0:
            return 0.0

        idle_duration = 0.0

        for previous, current in zip(
            timestamps,
            timestamps[1:]
        ):

            gap = current - previous

            if gap > self.IDLE_THRESHOLD:

                idle_duration += gap

        idle_ratio = (
            idle_duration
            / total_duration
        )

        # Keep the value within [0, 1].
        return min(
            max(idle_ratio, 0.0),
            1.0
        )

    @staticmethod
    def _average(values):
        """
        Calculate average of valid values.
        """

        if not values:
            return 0.0

        valid_values = [
            float(value)
            for value in values
            if FeatureExtractor._valid_value(value)
        ]

        if not valid_values:
            return 0.0

        return sum(valid_values) / len(valid_values)

    @staticmethod
    def _valid_value(value):
        """
        Check whether a feature value is a valid
        non-negative finite number.
        """

        if value is None:
            return False

        if not isinstance(value, (int, float)):
            return False

        if not math.isfinite(value):
            return False

        if value < 0:
            return False

        return True