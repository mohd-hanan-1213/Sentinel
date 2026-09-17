from pathlib import Path

from security.encryption import EncryptionManager


def main():
    manager = EncryptionManager()

    manager.initialize_key()

    original = b"SENTINEL confidential security data"

    encrypted = manager.encrypt_data(original)
    decrypted = manager.decrypt_data(encrypted)

    print("Original :", original)
    print("Encrypted:", encrypted)
    print("Decrypted:", decrypted)

    assert encrypted != original
    assert decrypted == original

    print("\nEncryption test PASSED")


if __name__ == "__main__":
    main()