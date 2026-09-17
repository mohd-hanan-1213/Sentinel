import os
import sys
import time

from PySide6.QtWidgets import QApplication,QDialog

from src.local_agent.collector.keyboard_collector import Keyboard_collector
from src.local_agent.collector.mouse_collector import Mouse_collector
from src.local_agent.buffer.event_buffer import EventBuffer
from src.local_agent.features.feature_extractor import FeatureExtractor
from src.local_agent.profile.behavioral_profile import BehavioralProfile
from src.local_agent.integration.pipeline import SentinelPipeline
from src.local_agent.integration.enrollment import EnrollmentManager
from src.local_agent.database.connection import SessionLocal

SAMPLE_INTERVAL = 30


def is_enrollment_mode():
    return "--enroll" in sys.argv


def run_sentinel_recovery(pipeline):
    """
    Display the unskippable Sentinel authentication window.

    The user must successfully authenticate with Sentinel credentials
    before the behavioral lock can be released.

    Returns:
        AuthenticationResult or None
    """

    from src.local_agent.response.sentinel_recovery import (
        SentinelRecoveryDialog
    )

    app = QApplication.instance()

    owns_app = False

    if app is None:
        app = QApplication(sys.argv)
        owns_app = True

    recovery = SentinelRecoveryDialog(
        pipeline.behavioral_lock
    )

    result = recovery.exec()


    if result == QDialog.DialogCode.Accepted:        
        authenticated_user = getattr(
            recovery,
            "authenticated_user",
            None
        )

        if authenticated_user is not None:
            if owns_app:
                # Do not quit yet if the admin dashboard will be opened.
                pass

            return authenticated_user

    if owns_app:
        app.quit()

    return None


def launch_admin_dashboard(authenticated_user):
    """
    Launch the admin dashboard only when the authenticated
    Sentinel account has ADMIN privileges.
    """

    if authenticated_user is None:
        return

    role = getattr(authenticated_user, "role", None)

    if role != "ADMIN":
        return

    from src.local_agent.admin.dashboard import Dashboard
    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    dashboard = Dashboard(
        admin_id=authenticated_user.user_id
    )

    # Keep a reference so Qt does not destroy the window.
    dashboard.show()

    app.exec()


def main():

    enrollment_mode = is_enrollment_mode()

    # ---------------------------------------------------------
    # Core components
    # ---------------------------------------------------------

    event_buffer = EventBuffer()
    feature_extractor = FeatureExtractor()
    behavioral_profile = BehavioralProfile()

    enrollment_manager = None
    pipeline = None
    session_id = None

    # ---------------------------------------------------------
    # Enrollment mode
    # ---------------------------------------------------------

    if enrollment_mode:

        print("=" * 60)
        print("SENTINEL BEHAVIORAL ENROLLMENT")
        print("=" * 60)

        enrollment_manager = EnrollmentManager()

        print("Enrollment mode active.")
        print("Collecting behavioral samples...")
        print("Move the mouse and type normally.")
        print()

    # ---------------------------------------------------------
    # Normal monitoring mode
    # ---------------------------------------------------------

    else:

        pipeline = SentinelPipeline(
            session_factory=SessionLocal
        )

        user_id = os.getenv("SENTINEL_USER_ID")

        if user_id:
            try:
                session_id = pipeline.start_session(
                    int(user_id)
                )

                print(
                    f"Sentinel monitoring session started: "
                    f"{session_id}"
                )

            except Exception as exc:
                print(
                    f"Warning: could not start database session: {exc}"
                )

        else:
            print(
                "Warning: SENTINEL_USER_ID is not configured."
            )

        print("=" * 60)
        print("SENTINEL BEHAVIORAL AUTHENTICATION ACTIVE")
        print("=" * 60)
        print()

    # ---------------------------------------------------------
    # Event handler
    # ---------------------------------------------------------

    def handle_event(event):
        event_buffer.add_event(event)

    # ---------------------------------------------------------
    # Start collectors
    # ---------------------------------------------------------

    keyboard_collector = Keyboard_collector(
        handle_event
    )

    mouse_collector = Mouse_collector(
        handle_event
    )

    keyboard_collector.start()
    mouse_collector.start()

    print("Keyboard collector started.")
    print("Mouse collector started.")
    print()

    # ---------------------------------------------------------
    # Monitoring loop
    # ---------------------------------------------------------

    last_sample_time = time.time()

    try:

        while True:

            time.sleep(1)

            current_time = time.time()

            if current_time - last_sample_time < SAMPLE_INTERVAL:
                continue

            last_sample_time = current_time

            # -------------------------------------------------
            # Get events from buffer
            # -------------------------------------------------

            events = event_buffer.get_all_events()

            if not events:
                continue

            # -------------------------------------------------
            # Extract behavioral features
            # -------------------------------------------------

            features = feature_extractor.extract(
                events
            )

            # -------------------------------------------------
            # Enrollment
            # -------------------------------------------------

            if enrollment_mode:

                enrollment_manager.add_sample(
                    features
                )

                sample_count = len(
                    enrollment_manager.samples
                )

                print(
                    f"Enrollment sample collected: "
                    f"{sample_count}"
                )

                # Check whether enrollment is complete
                if enrollment_manager.is_ready():

                    print()
                    print(
                        "Enrollment requirements satisfied."
                    )

                    enrollment_manager.train_model()

                    print(
                        "Behavioral model trained successfully."
                    )

                    print(
                        "You can now restart Sentinel "
                        "without --enroll."
                    )

                    break

                continue

            # -------------------------------------------------
            # NORMAL SENTINEL PIPELINE
            # -------------------------------------------------

            decision = pipeline.process_features(
                session_id,
                features
            )

            ml_output = decision["ml_output"]
            risk_result = decision["risk"]
            response = decision["response"]

            # -------------------------------------------------
            # Display monitoring information
            # -------------------------------------------------

            print("-" * 60)

            print(
                f"Anomaly Score : "
                f"{ml_output.get('anomaly_score', 0):.4f}"
            )

            print(
                f"Confidence    : "
                f"{ml_output.get('confidence', 0):.4f}"
            )

            print(
                f"Risk Score    : "
                f"{risk_result.get('risk_score', 0):.2f}"
            )

            print(
                f"Risk Level    : "
                f"{risk_result.get('risk_level')}"
            )

            print(
                f"Response      : "
                f"{response.get('action')}"
            )

            print(
                f"Monitoring    : "
                f"{response.get('monitoring_level')}"
            )

            print(
                f"Profile Update: "
                f"{response.get('profile_update_allowed')}"
            )

            # -------------------------------------------------
            # Update legitimate behavioral profile ONLY
            # -------------------------------------------------

            if response.get("profile_update_allowed"):

                behavioral_profile.add_sample(
                    features
                )

                print(
                    "Behavioral profile updated."
                )

            else:

                print(
                    "Behavioral profile NOT updated."
                )

            # -------------------------------------------------
            # CRITICAL RISK / BEHAVIORAL LOCK
            # -------------------------------------------------

            if response.get("lock_required"):

                print()
                print("=" * 60)
                print("SENTINEL BEHAVIORAL LOCK TRIGGERED")
                print("=" * 60)
                print()

                # The pipeline has already:
                #
                # 1. Set the behavioral lock state
                # 2. Captured encrypted camera evidence
                # 3. Persisted the risk/security event
                #
                # Now lock the Windows workstation.

                windows_locked = response.get(
                    "windows_locked",
                    False
                )

                if windows_locked:
                    print(
                        "Windows session locked."
                    )
                else:
                    print(
                        "Windows workstation lock "
                        "could not be activated."
                    )

                # -------------------------------------------------
                # Sentinel recovery authentication
                # -------------------------------------------------

                print(
                    "Waiting for Sentinel authentication..."
                )

                authenticated_user = run_sentinel_recovery(
                    pipeline
                )

                # -------------------------------------------------
                # Authentication failed / dialog closed
                # -------------------------------------------------

                if authenticated_user is None:

                    print(
                        "Sentinel authentication was not "
                        "completed."
                    )

                    # Keep the behavioral lock active.
                    #
                    # Do NOT continue normal monitoring.
                    #
                    # A failed/closed authentication window
                    # must not bypass the Sentinel lock.

                    if pipeline.behavioral_lock.is_locked():

                        print(
                            "Behavioral lock remains active."
                        )

                        # Re-open the authentication window.
                        while pipeline.behavioral_lock.is_locked():

                            authenticated_user = (
                                run_sentinel_recovery(
                                    pipeline
                                )
                            )

                            if authenticated_user is not None:
                                break

                    if pipeline.behavioral_lock.is_locked():

                        print(
                            "Sentinel authentication "
                            "still required."
                        )

                        continue

                # -------------------------------------------------
                # Successful Sentinel authentication
                # -------------------------------------------------

                if authenticated_user is not None:

                    print()
                    print("=" * 60)
                    print(
                        "SENTINEL AUTHENTICATION SUCCESSFUL"
                    )
                    print("=" * 60)

                    username = getattr(
                        authenticated_user,
                        "username",
                        None
                    )

                    role = getattr(
                        authenticated_user,
                        "role",
                        None
                    )

                    if username:
                        print(
                            f"Authenticated user: {username}"
                        )

                    if role:
                        print(
                            f"Role: {role}"
                        )

                    print()

                    # -------------------------------------------------
                    # ADMIN DASHBOARD
                    # -------------------------------------------------
                    #
                    # Only an authenticated ADMIN account can access
                    # the dashboard.
                    #
                    # Normal users are returned to normal operation.
                    #

                    if role == "ADMIN":

                        print(
                            "ADMIN account authenticated."
                        )

                        print(
                            "Loading Sentinel Admin Dashboard..."
                        )

                        launch_admin_dashboard(
                            authenticated_user
                        )

                        print(
                            "Admin dashboard closed."
                        )

                    else:

                        print(
                            "Authenticated account is not ADMIN."
                        )

                        print(
                            "Admin dashboard access denied."
                        )

                    print(
                        "Sentinel monitoring resumed."
                    )

                    print()

    except KeyboardInterrupt:

        print()
        print(
            "Sentinel monitoring stopped by user."
        )

    finally:

        # ---------------------------------------------------------
        # Stop collectors
        # ---------------------------------------------------------

        try:
            keyboard_collector.stop()
        except Exception:
            pass

        try:
            mouse_collector.stop()
        except Exception:
            pass

        # ---------------------------------------------------------
        # Close database session
        # ---------------------------------------------------------

        if session_id is not None and pipeline is not None:

            try:
                pipeline.end_session(
                    session_id
                )
            except Exception as exc:
                print(
                    f"Warning: could not close session: {exc}"
                )

        print(
            "Sentinel collectors stopped."
        )


if __name__ == "__main__":
    main()