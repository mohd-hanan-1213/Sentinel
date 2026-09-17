"""Administrator-only recovery dialog shown after a behavioral lock."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QKeyEvent
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class AdminUnlockDialog(QDialog):
    """Keep Sentinel paused until an administrator recovers its lock."""

    def __init__(self, behavioral_lock):
        super().__init__()
        self.behavioral_lock = behavioral_lock
        self.setWindowTitle("SENTINeL | Administrator recovery")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        root = QWidget()
        root.setObjectName("unlockRoot")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        panel = QFrame()
        panel.setObjectName("unlockPanel")
        panel.setFixedWidth(500)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(72, 54, 72, 46)
        layout.setSpacing(14)

        brand = QLabel("SENTINeL")
        brand.setObjectName("unlockBrand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("DEVICE LOCKED")
        title.setObjectName("unlockTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Critical behavioral risk detected. An administrator must authenticate to resume Sentinel.")
        subtitle.setObjectName("unlockSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        self.username = QLineEdit()
        self.username.setObjectName("unlockInput")
        self.username.setPlaceholderText("Administrator username")
        self.password = QLineEdit()
        self.password.setObjectName("unlockInput")
        self.password.setPlaceholderText("Administrator password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.returnPressed.connect(self.recover)
        self.status = QLabel("Windows was locked. Sign in to Windows, then complete Sentinel recovery.")
        self.status.setObjectName("unlockStatus")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setWordWrap(True)
        self.button = QPushButton("UNLOCK SENTINEL")
        self.button.setObjectName("unlockButton")
        self.button.clicked.connect(self.recover)

        layout.addWidget(brand)
        layout.addSpacing(8)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.status)
        layout.addSpacing(4)
        layout.addWidget(self.button)
        layout.addStretch()
        row.addWidget(panel)
        row.addStretch()
        root_layout.addLayout(row)
        root_layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(root)
        self.setStyleSheet("""
            #unlockRoot { background: #1E1E1E; }
            #unlockPanel { background: #171716; border: 1px solid #41413E; border-radius: 14px; }
            #unlockBrand { color: #A8F362; font: 700 18pt 'Lovine'; letter-spacing: 5px; }
            #unlockTitle { color: #F4F6FB; font: 700 18pt 'Segoe UI'; letter-spacing: 2px; }
            #unlockSubtitle, #unlockStatus { color: #C8CAC3; font: 9pt 'Segoe UI'; }
            #unlockInput { background: #1E1E1E; color: #F4F6FB; border: 1px solid #41413E; border-radius: 8px; padding: 11px; font: 10pt 'Segoe UI'; }
            #unlockInput:focus { border-color: #A8F362; }
            #unlockInput::placeholder { color: #94948F; }
            #unlockStatus[error='true'] { color: #FFB8B0; }
            #unlockButton { background: #A8F362; color: #171716; border: none; border-radius: 8px; padding: 12px; font: 700 10pt 'Segoe UI'; letter-spacing: 1px; }
            #unlockButton:hover { background: #C4FF8D; }
            #unlockButton:disabled { background: #52633D; color: #CCD7BE; }
        """)
        self.username.setFocus()

    def exec(self):
        """Present recovery as a full-screen overlay above all applications."""
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        return super().exec()

    def _set_status(self, message, error=False):
        self.status.setText(message)
        self.status.setProperty("error", error)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def recover(self):
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            self._set_status("Enter an administrator username and password.", True)
            (self.username if not username else self.password).setFocus()
            return

        self.button.setEnabled(False)
        self._set_status("Verifying administrator credentials...")
        result = self.behavioral_lock.recover(username, password)
        self.button.setEnabled(True)
        if result:
            self.accept()
            return

        self.password.clear()
        self._set_status("Recovery denied. An active administrator account is required.", True)
        self.password.setFocus()

    def reject(self):
        """The recovery dialog cannot be cancelled while Sentinel is locked."""

    def closeEvent(self, event: QCloseEvent):
        event.ignore()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
            return
        super().keyPressEvent(event)
