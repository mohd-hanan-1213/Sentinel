from pathlib import Path

from cryptography.fernet import Fernet


class EncryptionManager:
    """
    Handles encryption and decryption of sensitive Sentinel data.

    The Fernet key must be stored outside the source code.
    """

    def __init__(self, key_path: str = "security/sentinel.key"):
        self.key_path = Path(key_path)

    def generate_key(self) -> bytes:
        """
        Generate a new Fernet encryption key.
        """
        return Fernet.generate_key()

    def save_key(self, key: bytes) -> None:
        """
        Save the encryption key to the configured key file.
        """
        self.key_path.parent.mkdir(parents=True, exist_ok=True)

        self.key_path.write_bytes(key)

    def load_key(self) -> bytes:
        """
        Load the existing encryption key.
        """
        if not self.key_path.exists():
            raise FileNotFoundError(
                f"Encryption key not found: {self.key_path}"
            )

        return self.key_path.read_bytes()

    def initialize_key(self) -> None:
        """
        Generate and save a key if one does not already exist.
        """
        if not self.key_path.exists():
            key = self.generate_key()
            self.save_key(key)

    def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt raw bytes.
        """
        key = self.load_key()
        cipher = Fernet(key)

        return cipher.encrypt(data)

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt previously encrypted bytes.
        """
        key = self.load_key()
        cipher = Fernet(key)

        return cipher.decrypt(encrypted_data)

    def encrypt_file(
        self,
        input_path: str,
        output_path: str,
    ) -> None:
        """
        Encrypt a file and save the encrypted result.
        """
        input_file = Path(input_path)
        output_file = Path(output_path)

        data = input_file.read_bytes()
        encrypted_data = self.encrypt_data(data)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(encrypted_data)

    def decrypt_file(
        self,
        input_path: str,
        output_path: str,
    ) -> None:
        """
        Decrypt an encrypted file.
        """
        input_file = Path(input_path)
        output_file = Path(output_path)

        encrypted_data = input_file.read_bytes()
        decrypted_data = self.decrypt_data(encrypted_data)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(decrypted_data)