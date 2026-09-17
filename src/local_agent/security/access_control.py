from dataclasses import dataclass

from src.local_agent.authentication.sentinel_auth import (
    SentinelAuthenticator,
    AuthenticationResult,
)


@dataclass
class AccessResult:
    """
    Result of an access-control decision.
    """

    allowed: bool
    user_id: int | None = None
    username: str | None = None
    role: str | None = None
    resource: str = ""
    message: str = ""


class AccessController:
    """
    Controls access to Sentinel-protected resources.

    Authentication is delegated to SentinelAuthenticator.
    This class handles authorization decisions.
    """

    ADMIN_ROLE = "ADMIN"

    BEHAVIORAL_LOCK = "BEHAVIORAL_LOCK"
    ADMIN_DASHBOARD = "ADMIN_DASHBOARD"
    SECURITY_EVIDENCE = "SECURITY_EVIDENCE"

    def __init__(self):
        self.authenticator = SentinelAuthenticator()

    def authenticate(
        self,
        username: str,
        password: str,
        authentication_type: str = "SENTINEL_LOGIN",
    ) -> AuthenticationResult:
        """
        Authenticate a user using the existing Sentinel authentication system.
        """
        return self.authenticator.authenticate(
            username=username,
            password=password,
            authentication_type=authentication_type,
        )

    def authorize_behavioral_lock_recovery(
        self,
        username: str,
        password: str,
    ) -> AccessResult:
        """
        Authenticate a user for behavioral-lock recovery.

        Only an active administrator can recover the behavioral lock.
        """

        result = self.authenticate(
            username=username,
            password=password,
            authentication_type="BEHAVIORAL_LOCK_RECOVERY",
        )

        if not result.success:
            return AccessResult(
                allowed=False,
                resource=self.BEHAVIORAL_LOCK,
                message="Behavioral lock recovery denied.",
            )

        if result.role != self.ADMIN_ROLE:
            return AccessResult(
                allowed=False,
                user_id=result.user_id,
                username=result.username,
                role=result.role,
                resource=self.BEHAVIORAL_LOCK,
                message="Administrator privileges are required to recover the behavioral lock.",
            )

        return AccessResult(
            allowed=True,
            user_id=result.user_id,
            username=result.username,
            role=result.role,
            resource=self.BEHAVIORAL_LOCK,
            message="Behavioral lock recovery authorized.",
        )

    def authorize_admin_dashboard(
        self,
        username: str,
        password: str,
    ) -> AccessResult:
        """
        Authenticate and authorize an administrator for the admin dashboard.
        """

        result = self.authenticate(
            username=username,
            password=password,
            authentication_type="ADMIN_DASHBOARD_LOGIN",
        )

        if not result.success:
            return AccessResult(
                allowed=False,
                resource=self.ADMIN_DASHBOARD,
                message="Admin dashboard access denied.",
            )

        if result.role != self.ADMIN_ROLE:
            return AccessResult(
                allowed=False,
                user_id=result.user_id,
                username=result.username,
                role=result.role,
                resource=self.ADMIN_DASHBOARD,
                message="Administrator privileges required.",
            )

        return AccessResult(
            allowed=True,
            user_id=result.user_id,
            username=result.username,
            role=result.role,
            resource=self.ADMIN_DASHBOARD,
            message="Admin dashboard access authorized.",
        )

    def authorize_security_evidence(
        self,
        username: str,
        password: str,
    ) -> AccessResult:
        """
        Authenticate and authorize an administrator to access
        encrypted security evidence.
        """

        result = self.authenticate(
            username=username,
            password=password,
            authentication_type="SECURITY_EVIDENCE_ACCESS",
        )

        if not result.success:
            return AccessResult(
                allowed=False,
                resource=self.SECURITY_EVIDENCE,
                message="Security evidence access denied.",
            )

        if result.role != self.ADMIN_ROLE:
            return AccessResult(
                allowed=False,
                user_id=result.user_id,
                username=result.username,
                role=result.role,
                resource=self.SECURITY_EVIDENCE,
                message="Administrator privileges required.",
            )

        return AccessResult(
            allowed=True,
            user_id=result.user_id,
            username=result.username,
            role=result.role,
            resource=self.SECURITY_EVIDENCE,
            message="Security evidence access authorized.",
        )
