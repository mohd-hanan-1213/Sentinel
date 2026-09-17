from getpass import getpass

from authentication.password import PasswordManager
from database.connection import SessionLocal
from database.models import SentinelCredential, User


def create_admin():
    username = input("Enter Sentinel admin username: ").strip()

    if not username:
        print("Username cannot be empty.")
        return

    password = getpass("Enter Sentinel admin password: ")
    confirm_password = getpass("Confirm Sentinel admin password: ")

    if not password:
        print("Password cannot be empty.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    password_manager = PasswordManager()

    with SessionLocal() as db:
        existing_user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if existing_user:
            print("A user with that username already exists.")
            return

        password_hash = password_manager.hash_password(password)

        user = User(
            username=username,
            role="ADMIN",
            status="ACTIVE",
        )

        db.add(user)
        db.flush()

        credential = SentinelCredential(
            user_id=user.id,
            password_hash=password_hash,
            status="ACTIVE",
        )

        db.add(credential)
        db.commit()

        print()
        print("Sentinel administrator created successfully.")
        print(f"Username: {username}")
        print("Role: ADMIN")
        print("Password: stored as an Argon2 hash.")


if __name__ == "__main__":
    create_admin()