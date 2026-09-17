"""Webcam evidence capture and encrypted evidence-file lifecycle."""

from datetime import datetime
from pathlib import Path
import os

from src.local_agent.security.encryption import EncryptionManager


class CameraEvidenceService:
    def __init__(self, storage_dir="data/evidence", camera_index=0,
                 encryption_manager=None):
        self.storage_dir = Path(storage_dir)
        self.camera_index = camera_index
        self.encryption_manager = encryption_manager or EncryptionManager()

    def camera_available(self):
        """Return whether the configured webcam can be opened right now."""
        import cv2
        camera = self._open_camera(cv2)
        try:
            return bool(camera.isOpened())
        finally:
            camera.release()

    def capture_encrypted_image(self, timestamp=None):
        """Capture one frame, encrypt it, and never retain plaintext."""
        import cv2
        timestamp = timestamp or datetime.utcnow()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        stem = timestamp.strftime("%Y%m%dT%H%M%S_%f")
        plain_path = self.storage_dir / f"{stem}.jpg"
        encrypted_path = self.storage_dir / f"{stem}.jpg.fernet"
        camera = self._open_camera(cv2)
        try:
            if not camera.isOpened():
                return None
            ok, frame = camera.read()
            if not ok:
                return None
            if not cv2.imwrite(str(plain_path), frame):
                return None
            self.encryption_manager.initialize_key()
            self.encryption_manager.encrypt_file(plain_path, encrypted_path)
            return encrypted_path
        finally:
            camera.release()
            if plain_path.exists():
                plain_path.unlink()

    def _open_camera(self, cv2):
        """Try the Windows camera backends before OpenCV's generic fallback."""
        if os.name == "nt":
            for backend in (cv2.CAP_DSHOW, cv2.CAP_MSMF):
                camera = cv2.VideoCapture(self.camera_index, backend)
                if camera.isOpened():
                    return camera
                camera.release()
        return cv2.VideoCapture(self.camera_index)

    @staticmethod
    def delete_file(file_reference):
        path = Path(file_reference)
        if path.exists():
            path.unlink()
