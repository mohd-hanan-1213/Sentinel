from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError


class PasswordManager:
    """
    Handles Sentinel password hashing and verification.

    Passwords are never stored in plaintext.
    """

    def __init__(self):
        self._hasher = PasswordHasher()

    def hash_password(self, password: str) -> str:
        """
        Hash a plaintext password using Argon2.
        """
        if not password:
            raise ValueError("Password cannot be empty.")

        return self._hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify a plaintext password against an Argon2 hash.
        """
        if not password or not password_hash:
            return False

        try:
            return self._hasher.verify(password_hash, password)

        except (VerifyMismatchError, VerificationError):
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        """
        Check whether the stored hash should be upgraded.
        """
        return self._hasher.check_needs_rehash(password_hash)