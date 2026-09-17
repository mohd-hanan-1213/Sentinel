from enum import Enum

import ctypes
import os

# from src.local_agent.security.access_control import AccessController


class LockState(Enum):
    UNLOCKED = "UNLOCKED"
    LOCKED = "LOCKED"


class BehavioralLock:
    """
    Controls the Sentinel behavioral lock.

    The lock is separate from the normal Windows password.
    Recovery is performed through Sentinel authentication.
    """

    def __init__(self, access_controller=None):
        self.state = LockState.UNLOCKED

        if access_controller is not None:
            self.access_controller = access_controller
        else:
            from src.local_agent.security.access_control import AccessController

            self.access_controller = AccessController()

    def lock(self) -> None:

        """
        Activate the behavioral lock.
        """
        self.state = LockState.LOCKED

    def lock_windows_session(self) -> bool:
        """Lock Windows when supported; Sentinel's application lock remains."""
        if os.name != "nt":
            return False

        try:
            return bool(ctypes.windll.user32.LockWorkStation())
        except (AttributeError, OSError):
            return False

    def unlock(self) -> None:
        """
        Release the behavioral lock.

        This method is intended to be called only after
        successful Sentinel authentication.
        """
        self.state = LockState.UNLOCKED

    def is_locked(self) -> bool:
        """
        Return whether the behavioral lock is currently active.
        """
        return self.state == LockState.LOCKED

    def get_state(self) -> str:
        """
        Return the current lock state.
        """
        return self.state.value

    def recover(self, username, password):
        """
        Authenticate the user using Sentinel authentication.

        Returns:
            AccessResult from AccessController.
        """

        if not self.is_locked():
            return self.access_controller.authorize_behavioral_lock_recovery(
                username,
                password,
            )

        result = self.access_controller.authorize_behavioral_lock_recovery(
            username,
            password,
        )

        if result.allowed:
            self.unlock()

        return result
