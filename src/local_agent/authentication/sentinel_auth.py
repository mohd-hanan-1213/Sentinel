from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select

from authentication.password import PasswordManager
from database.connection import SessionLocal
from database.models import (
    AuthenticationEvent,
    SentinelCredential,
    User,
)


@dataclass
class AuthenticationResult:
    success: bool
    user_id: int | None = None
    username: str | None = None
    role: str | None = None
    message: str = ""


class SentinelAuthenticator:
    """
    Handles Sentinel authentication.

    This authentication is separate from the Windows password.
    The same Sentinel credential can be used for:
      - Behavioral lock recovery
      - Administrator authentication
    """

    def __init__(self):
        self.password_manager = PasswordManager()

    def authenticate(
        self,
        username: str,
        password: str,
        authentication_type: str = "SENTINEL_LOGIN",
    ) -> AuthenticationResult:

        if not username or not password:
            return AuthenticationResult(
                success=False,
                message="Username and password are required.",
            )

        with SessionLocal() as db:
            user = db.scalar(
                select(User).where(
                    User.username == username,
                    User.status == "ACTIVE",
                )
            )

            if user is None:
                self._record_authentication_event(
                    db=db,
                    user_id=None,
                    authentication_type=authentication_type,
                    result="FAILURE",
                )

                db.commit()

                return AuthenticationResult(
                    success=False,
                    message="Authentication failed.",
                )

            credential = db.scalar(
                select(SentinelCredential).where(
                    SentinelCredential.user_id == user.id,
                    SentinelCredential.status == "ACTIVE",
                )
            )

            if credential is None:
                self._record_authentication_event(
                    db=db,
                    user_id=user.id,
                    authentication_type=authentication_type,
                    result="FAILURE",
                )

                db.commit()

                return AuthenticationResult(
                    success=False,
                    message="Authentication failed.",
                )

            password_valid = self.password_manager.verify_password(
                password,
                credential.password_hash,
            )

            if not password_valid:
                self._record_authentication_event(
                    db=db,
                    user_id=user.id,
                    authentication_type=authentication_type,
                    result="FAILURE",
                )

                db.commit()

                return AuthenticationResult(
                    success=False,
                    message="Authentication failed.",
                )

            self._record_authentication_event(
                db=db,
                user_id=user.id,
                authentication_type=authentication_type,
                result="SUCCESS",
            )

            db.commit()

            return AuthenticationResult(
                success=True,
                user_id=user.id,
                username=user.username,
                role=user.role,
                message="Authentication successful.",
            )

    @staticmethod
    def _record_authentication_event(
        db,
        user_id: int | None,
        authentication_type: str,
        result: str,
    ) -> None:

        event = AuthenticationEvent(
            user_id=user_id,
            session_id=None,
            timestamp=datetime.utcnow(),
            authentication_type=authentication_type,
            result=result,
            attempt_count=1,
        )

        db.add(event)