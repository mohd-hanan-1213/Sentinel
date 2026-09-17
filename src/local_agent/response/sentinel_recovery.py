"""Unskippable Sentinel behavioral-lock recovery window."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.local_agent.security.access_control import AccessController


class SentinelRecoveryDialog(QDialog):
    """
    Modal Sentinel authentication dialog.

    The dialog cannot be closed until valid Sentinel
    credentials are supplied.
    """

    def __init__(self, behavioral_lock, parent=None):
        super().__init__(parent)

        self.behavioral_lock = behavioral_lock
        self.authenticated = False
        self.authenticated_user = None

        self.setWindowTitle("Sentinel Behavioral Lock")

        # --------------------------------------------------
        # WINDOW BEHAVIOUR
        # --------------------------------------------------

        self.setWindowModality(
            Qt.WindowModality.ApplicationModal
        )

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        # Full-screen lock state.
        self.setWindowState(
            Qt.WindowState.WindowFullScreen
        )

        # No close button is provided.
        # ApplicationModal prevents normal interaction
        # with the underlying Sentinel application.

        # --------------------------------------------------
        # TITLE
        # --------------------------------------------------

        title = QLabel(
            "SENTINEL BEHAVIORAL LOCK"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #005f82;
                padding: 10px;
            }
            """
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # --------------------------------------------------
        # MESSAGE
        # --------------------------------------------------

        message = QLabel(
            "Critical suspicious behaviour was detected.\n\n"
            "Sentinel authentication is required before "
            "normal PC operation can continue."
        )

        message.setWordWrap(True)

        message.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        message.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #303840;
                padding: 10px;
            }
            """
        )

        # --------------------------------------------------
        # USERNAME
        # --------------------------------------------------

        username_label = QLabel(
            "Sentinel Username"
        )

        self.username = QLineEdit()

        self.username.setPlaceholderText(
            "Enter Sentinel username"
        )

        self.username.setMinimumHeight(42)

        # --------------------------------------------------
        # PASSWORD
        # --------------------------------------------------

        password_label = QLabel(
            "Sentinel Password"
        )

        self.password = QLineEdit()

        self.password.setPlaceholderText(
            "Enter Sentinel password"
        )

        self.password.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.password.setMinimumHeight(42)

        # --------------------------------------------------
        # STATUS
        # --------------------------------------------------

        self.status = QLabel("")

        self.status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status.setStyleSheet(
            """
            QLabel {
                color: #d93025;
                font-size: 13px;
            }
            """
        )

        # --------------------------------------------------
        # AUTHENTICATE BUTTON
        # --------------------------------------------------

        self.authenticate_button = QPushButton(
            "AUTHENTICATE"
        )

        self.authenticate_button.setMinimumHeight(48)

        self.authenticate_button.setStyleSheet(
            """
            QPushButton {
                background-color: #005f82;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #004c68;
            }

            QPushButton:pressed {
                background-color: #003a50;
            }
            """
        )

        self.authenticate_button.clicked.connect(
            self.authenticate
        )

        self.password.returnPressed.connect(
            self.authenticate
        )

        # --------------------------------------------------
        # LAYOUT
        # --------------------------------------------------

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            35, 25, 35, 25
        )

        layout.setSpacing(10)

        layout.addWidget(title)
        layout.addWidget(message)

        layout.addWidget(username_label)
        layout.addWidget(self.username)

        layout.addWidget(password_label)
        layout.addWidget(self.password)

        layout.addWidget(self.status)
        layout.addWidget(self.authenticate_button)

        self.setLayout(layout)

    # ======================================================
    # FORCE FULL SCREEN WHEN WINDOW IS SHOWN
    # ======================================================

    def showEvent(self, event):
        """
        Force Sentinel recovery into true full-screen mode
        whenever the lock window is displayed.
        """

        super().showEvent(event)

        screen = self.screen()

        if screen is None:
            screen = QApplication.primaryScreen()

        if screen is not None:

            self.setGeometry(
                screen.geometry()
            )

        self.setWindowState(
            self.windowState()
            | Qt.WindowState.WindowFullScreen
        )

        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    # ======================================================
    # AUTHENTICATION
    # ======================================================

    def authenticate(self):

        username = self.username.text().strip()
        password = self.password.text()

        if not username or not password:

            self.status.setText(
                "Sentinel username and password are required."
            )

            return

        self.authenticate_button.setEnabled(False)

        self.status.setText(
            "Authenticating..."
        )

        QApplication.processEvents()

        try:

            result = (
                self.behavioral_lock.recover(
                    username=username,
                    password=password,
                )
            )

        except Exception as error:

            self.authenticate_button.setEnabled(True)

            self.status.setText(
                f"Authentication error: {error}"
            )

            return

        # --------------------------------------------------
        # SUCCESSFUL SENTINEL AUTHENTICATION
        # --------------------------------------------------

        if result.allowed:

            self.authenticated = True

            # Save authenticated Sentinel account.
            self.authenticated_user = result

            self.accept()

            return

        # --------------------------------------------------
        # FAILED AUTHENTICATION
        # --------------------------------------------------

        self.password.clear()

        self.authenticate_button.setEnabled(True)

        self.status.setText(
            result.message
            or "Invalid Sentinel credentials. "
            "The PC remains locked."
        )

        self.password.setFocus()

    # ======================================================
    # PREVENT ESC / CLOSE
    # ======================================================

    def reject(self):
        """
        Prevent the dialog from being closed with Esc,
        Alt+F4, or other normal dialog rejection.
        """

        if self.authenticated:

            super().reject()

        # Otherwise deliberately do nothing.

    def closeEvent(self, event):
        """
        Prevent closing the recovery window while locked.
        """

        if self.authenticated:

            event.accept()

        else:

            event.ignore()


def require_sentinel_authentication(behavioral_lock):

    """
    Display the unskippable Sentinel recovery window.

    Returns True only after successful authentication.
    """

    app = QApplication.instance()

    owns_application = False

    if app is None:

        app = QApplication([])

        owns_application = True

    dialog = SentinelRecoveryDialog(
        behavioral_lock
    )

    # Explicitly force full-screen before execution.
    dialog.showFullScreen()
    dialog.raise_()
    dialog.activateWindow()

    result = dialog.exec()

    success = (
        result == QDialog.DialogCode.Accepted
        and not behavioral_lock.is_locked()
    )

    if owns_application:

        app.quit()

    return success