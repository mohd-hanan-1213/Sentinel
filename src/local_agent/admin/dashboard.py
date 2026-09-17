"""Administrator-only PySide6 dashboard for Sentinel."""
import sys
from datetime import UTC, datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from sqlalchemy import select

from src.local_agent.database.connection import SessionLocal
from src.local_agent.database.models import AuditLog, Evidence, RiskEvent, SecurityEvent, Session
from src.local_agent.camera.evidence import CameraEvidenceService
from src.local_agent.security.access_control import AccessController
from src.local_agent.security.encryption import EncryptionManager


class Login(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SENTINeL | Secure sign in")
        self.setFixedSize(520, 580)
        self.setModal(True)

        root = QWidget()
        root.setObjectName("loginRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(82, 60, 82, 52)
        layout.setSpacing(14)
        brand = QLabel("SENTINeL")
        brand.setObjectName("loginBrand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("ADMINISTRATOR LOGIN")
        title.setObjectName("loginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Secure access to the Sentinel security console")
        subtitle.setObjectName("loginSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username = QLineEdit()
        self.username.setObjectName("loginInput")
        self.username.setPlaceholderText("Username")
        self.username.setClearButtonEnabled(True)
        username_row = self._input_row("U", self.username)

        self.password = QLineEdit()
        self.password.setObjectName("loginInput")
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.returnPressed.connect(self.login)
        self.show_password = QPushButton("Show")
        self.show_password.setObjectName("showPassword")
        self.show_password.setCheckable(True)
        self.show_password.toggled.connect(self._toggle_password)
        password_row = self._input_row("L", self.password, self.show_password)

        self.status = QLabel("Protected by continuous identity verification")
        self.status.setObjectName("loginStatus")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button = QPushButton("LOGIN")
        self.button.setObjectName("loginButton")
        self.button.clicked.connect(self.login)
        footer = QLabel("Security activity is recorded for this session")
        footer.setObjectName("loginFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(brand)
        layout.addSpacing(12)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(24)
        layout.addWidget(username_row)
        layout.addWidget(password_row)
        layout.addWidget(self.status)
        layout.addSpacing(6)
        layout.addWidget(self.button)
        layout.addStretch()
        layout.addWidget(footer)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(root)
        self.setStyleSheet("""
            #loginRoot { background: #1E1E1E; }
            #loginBrand { color: #A8F362; font: 700 18pt 'Lovine'; letter-spacing: 5px; }
            #loginTitle { color: #F4F6FB; font: 700 18pt 'Segoe UI'; letter-spacing: 2px; }
            #loginSubtitle { color: #C8CAC3; font: 9pt 'Segoe UI'; }
            #inputRow { background: #171716; border: 1px solid #41413E; border-radius: 24px; min-height: 48px; }
            #inputIcon { color: #171716; background: #F4F6FB; border-radius: 18px; min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; font: 700 11pt 'Segoe UI'; }
            #loginInput { background: transparent; border: none; color: #F4F6FB; padding: 8px 2px; font: 10.5pt 'Segoe UI'; }
            #loginInput::placeholder { color: #94948F; }
            #showPassword { background: transparent; color: #F4F6FB; border: none; padding: 6px 10px; font: 700 8pt 'Segoe UI'; }
            #showPassword:hover { color: #A8F362; }
            #loginStatus { color: #C8CAC3; font: 8.5pt 'Segoe UI'; min-height: 22px; }
            #loginStatus[error='true'] { color: #FFB8B0; }
            #loginButton { background: #A8F362; color: #171716; border: none; border-radius: 24px; padding: 13px; font: 700 11pt 'Segoe UI'; letter-spacing: 1px; }
            #loginButton:hover { background: #C4FF8D; }
            #loginButton:pressed { background: #82C63E; }
            #loginButton:disabled { background: #52633D; color: #CCD7BE; }
            #loginFooter { color: #94948F; font: 8pt 'Segoe UI'; }
        """)
        self.admin_id = None
        self.username.setFocus()

    @staticmethod
    def _input_row(icon_text, field, trailing=None):
        row = QFrame()
        row.setObjectName("inputRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(7, 5, 9, 5)
        icon = QLabel(icon_text)
        icon.setObjectName("inputIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        layout.addWidget(field)
        if trailing:
            layout.addWidget(trailing)
        return row

    def _toggle_password(self, visible):
        self.password.setEchoMode(QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password)
        self.show_password.setText("Hide" if visible else "Show")

    def _set_status(self, message, error=False):
        self.status.setText(message)
        self.status.setProperty("error", error)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def login(self):
        username, password = self.username.text().strip(), self.password.text()
        if not username or not password:
            self._set_status("Enter your username and password to continue.", True)
            (self.username if not username else self.password).setFocus()
            return
        self.button.setEnabled(False)
        self._set_status("Verifying secure credentials...")
        QApplication.processEvents()
        result = AccessController().authorize_admin_dashboard(username, password)
        self.button.setEnabled(True)
        if result.allowed:
            self.admin_id = result.user_id
            self.accept()
            return
        self.password.clear()
        self._set_status(result.message or "Access denied. Check your credentials and try again.", True)
        self.password.setFocus()


class Dashboard(QMainWindow):
    def __init__(self, admin_id):
        super().__init__()
        self.admin_id = admin_id
        self.setWindowTitle("SENTINeL | Security Console")
        self.resize(1120, 700)
        root = QWidget(); root.setObjectName("dashboardRoot")
        root_layout = QVBoxLayout(root); root_layout.setContentsMargins(26, 22, 26, 22); root_layout.setSpacing(16)
        self.setCentralWidget(root)
        header = QFrame(); header.setObjectName("consoleHeader")
        header_layout = QHBoxLayout(header); header_layout.setContentsMargins(20, 15, 20, 15)
        heading = QVBoxLayout()
        title = QLabel("SENTINeL SECURITY CONSOLE"); title.setObjectName("consoleTitle")
        subtitle = QLabel("Live behavioral security monitoring"); subtitle.setObjectName("consoleSubtitle")
        heading.addWidget(title); heading.addWidget(subtitle)
        self.refresh_button = QPushButton("Refresh"); self.refresh_button.setObjectName("consoleButton"); self.refresh_button.clicked.connect(self.refresh)
        header_layout.addLayout(heading); header_layout.addStretch(); header_layout.addWidget(self.refresh_button)
        root_layout.addWidget(header)
        self.tabs = QTabWidget(); self.tabs.setObjectName("consoleTabs")
        self.summary = self._build_overview()
        self.risks = self.table(["Time", "Session", "Score", "Level", "Response"])
        self.sessions = self.table(["ID", "User", "Started", "Ended", "State"])
        self.alerts = self.table(["Time", "Session", "Severity", "Event", "State"])
        self.photos = self.table(["ID", "Time", "Session", "Risk event", "Retention"])
        for name, widget in (("Overview", self.summary), ("Risk events", self.risks), ("Sessions", self.sessions), ("Alerts", self.alerts), ("Evidence", self.photos)):
            page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(8, 12, 8, 8); layout.addWidget(widget); self.tabs.addTab(page, name)
        actions = QHBoxLayout(); actions.addStretch()
        view = QPushButton("View encrypted photo"); view.setObjectName("consoleButton"); view.clicked.connect(self.view_photo)
        delete = QPushButton("Delete photo"); delete.setObjectName("dangerButton"); delete.clicked.connect(self.delete_photo)
        actions.addWidget(view); actions.addWidget(delete); self.tabs.widget(4).layout().addLayout(actions)
        root_layout.addWidget(self.tabs)
        self.setStyleSheet("""
            #dashboardRoot { background: #1E1E1E; }
            #consoleHeader { background: #171716; border: 1px solid #41413E; border-radius: 12px; }
            #consoleTitle { color: #A8F362; font: 700 18pt 'Orbitron'; letter-spacing: 1px; }
            #consoleSubtitle { color: #C8CAC3; font: 9pt 'Segoe UI'; }
            #consoleButton { background: #A8F362; color: #171716; border: none; border-radius: 7px; padding: 9px 16px; font: 700 9pt 'Segoe UI'; }
            #consoleButton:hover { background: #C4FF8D; }
            #consoleButton:pressed { background: #82C63E; }
            #dangerButton { background: #302522; color: #F4F6FB; border: 1px solid #A8F362; border-radius: 7px; padding: 9px 16px; font: 700 9pt 'Segoe UI'; }
            #dangerButton:hover { background: #49382F; }
            #consoleTabs::pane { background: #171716; border: 1px solid #41413E; border-radius: 10px; top: -1px; }
            #consoleTabs QTabBar::tab { background: #1E1E1E; color: #F4F6FB; border: 1px solid #41413E; border-bottom: none; border-radius: 7px 7px 0 0; padding: 10px 18px; margin-right: 4px; font: 600 9pt 'Segoe UI'; }
            #consoleTabs QTabBar::tab:hover { color: #A8F362; }
            #consoleTabs QTabBar::tab:selected { background: #A8F362; color: #171716; border-color: #A8F362; }
            #overviewCard, #metricCard { background: #1E1E1E; border: 1px solid #41413E; border-radius: 10px; }
            #overviewHeading { color: #A8F362; font: 700 13pt 'Orbitron'; }
            #overviewText { color: #F4F6FB; font: 9.5pt 'Segoe UI'; }
            #metricLabel { color: #C8CAC3; font: 700 8pt 'Segoe UI'; }
            #metricValue { color: #F4F6FB; font: 700 24pt 'Segoe UI'; }
            QTableWidget { background: #171716; alternate-background-color: #1E1E1E; color: #F4F6FB; border: none; gridline-color: #41413E; selection-background-color: #A8F362; selection-color: #171716; font: 9pt 'Segoe UI'; }
            QHeaderView::section { background: #1E1E1E; color: #F4F6FB; border: none; border-bottom: 1px solid #A8F362; padding: 10px; font: 700 8pt 'Segoe UI'; }
            QScrollBar:vertical { background: #171716; width: 10px; margin: 0; }
            QScrollBar::handle:vertical { background: #A8F362; min-height: 24px; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        self.refresh()

    def _build_overview(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(14)
        overview = QFrame(); overview.setObjectName("overviewCard")
        overview_layout = QVBoxLayout(overview); overview_layout.setContentsMargins(20, 17, 20, 17)
        heading = QLabel("Current security posture"); heading.setObjectName("overviewHeading")
        self.overview_text = QLabel(); self.overview_text.setObjectName("overviewText"); self.overview_text.setWordWrap(True)
        overview_layout.addWidget(heading); overview_layout.addWidget(self.overview_text)
        layout.addWidget(overview)
        metrics = QHBoxLayout(); metrics.setSpacing(12)
        self.metric_values = {}
        for key, label in (("decisions", "RECENT DECISIONS"), ("high", "HIGH RISK"), ("critical", "CRITICAL EVENTS"), ("alerts", "OPEN ALERTS")):
            card = QFrame(); card.setObjectName("metricCard")
            card_layout = QVBoxLayout(card); card_layout.setContentsMargins(16, 13, 16, 13)
            card_label = QLabel(label); card_label.setObjectName("metricLabel")
            value = QLabel("0"); value.setObjectName("metricValue")
            card_layout.addWidget(card_label); card_layout.addWidget(value)
            metrics.addWidget(card); self.metric_values[key] = value
        layout.addLayout(metrics)
        layout.addStretch()
        return page
    @staticmethod
    def table(headers):
        table = QTableWidget(0, len(headers)); table.setHorizontalHeaderLabels(headers); table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); return table
    @staticmethod
    def fill(table, rows):
        table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row): table.setItem(i, j, QTableWidgetItem("" if value is None else str(value)))
        table.resizeColumnsToContents()
    def refresh(self):
        with SessionLocal() as db:
            risks = db.scalars(select(RiskEvent).order_by(RiskEvent.timestamp.desc()).limit(200)).all(); sessions = db.scalars(select(Session).order_by(Session.started_at.desc()).limit(200)).all(); alerts = db.scalars(select(SecurityEvent).order_by(SecurityEvent.timestamp.desc()).limit(200)).all(); photos = db.scalars(select(Evidence).order_by(Evidence.timestamp.desc()).limit(200)).all()
            db.add(AuditLog(admin_id=self.admin_id, timestamp=datetime.now(UTC).replace(tzinfo=None), action="VIEW_DASHBOARD", resource_type="DASHBOARD")); db.commit()
        high_risk = sum(x.risk_level == 'HIGH' for x in risks)
        critical_risk = sum(x.risk_level == 'CRITICAL' for x in risks)
        open_alerts = sum(x.status == 'OPEN' for x in alerts)
        self.metric_values['decisions'].setText(str(len(risks)))
        self.metric_values['high'].setText(str(high_risk))
        self.metric_values['critical'].setText(str(critical_risk))
        self.metric_values['alerts'].setText(str(open_alerts))
        if critical_risk or open_alerts:
            self.overview_text.setText("Review recommended: there are critical security events or open alerts that require administrator attention.")
        elif high_risk:
            self.overview_text.setText("High-risk behavioral events are present. Open Risk events to review the recommended response.")
        else:
            self.overview_text.setText("Continuous trust is operating normally. No urgent signals are waiting for review.")
        self.fill(self.risks, [[x.timestamp,x.session_id,x.risk_score,x.risk_level,x.response] for x in risks]); self.fill(self.sessions, [[x.id,x.user_id,x.started_at,x.ended_at,x.status] for x in sessions]); self.fill(self.alerts, [[x.timestamp,x.session_id,x.severity,x.event_type,x.status] for x in alerts]); self.fill(self.photos, [[x.id,x.timestamp,x.session_id,x.risk_event_id,"Admin controlled"] for x in photos])
    def view_photo(self):
        row = self.photos.currentRow()
        if row < 0: return QMessageBox.information(self, "Sentinel", "Select evidence first.")
        evidence_id = int(self.photos.item(row, 0).text())
        with SessionLocal() as db:
            evidence = db.get(Evidence, evidence_id)
            try:
                with open(evidence.file_reference, "rb") as source: image = EncryptionManager().decrypt_data(source.read())
            except (FileNotFoundError, ValueError) as error: return QMessageBox.warning(self, "Evidence unavailable", str(error))
            db.add(AuditLog(admin_id=self.admin_id, timestamp=datetime.now(UTC).replace(tzinfo=None), action="VIEW_EVIDENCE", resource_type="EVIDENCE", resource_id=str(evidence_id))); db.commit()
        pixmap = QPixmap(); pixmap.loadFromData(image); label = QLabel(); label.setPixmap(pixmap.scaled(900,650,Qt.AspectRatioMode.KeepAspectRatio)); dialog = QDialog(self); dialog.setWindowTitle(f"Evidence {evidence_id}"); layout = QVBoxLayout(dialog); layout.addWidget(label); dialog.exec()
    def delete_photo(self):
        row = self.photos.currentRow()
        if row < 0: return QMessageBox.information(self, "Sentinel", "Select evidence first.")
        evidence_id = int(self.photos.item(row, 0).text())
        answer = QMessageBox.question(self, "Delete encrypted evidence", f"Permanently delete evidence {evidence_id}? This cannot be undone.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes: return
        with SessionLocal() as db:
            evidence = db.get(Evidence, evidence_id)
            if evidence is None: return QMessageBox.warning(self, "Sentinel", "Evidence no longer exists.")
            try:
                CameraEvidenceService.delete_file(evidence.file_reference)
            except OSError as error:
                return QMessageBox.warning(self, "Delete failed", str(error))
            db.add(AuditLog(admin_id=self.admin_id, timestamp=datetime.now(UTC).replace(tzinfo=None), action="DELETE_EVIDENCE", resource_type="EVIDENCE", resource_id=str(evidence_id)))
            db.delete(evidence); db.commit()
        self.refresh()


def main():
    app = QApplication(sys.argv); login = Login()
    if login.exec() != QDialog.DialogCode.Accepted: return 1
    dashboard = Dashboard(login.admin_id); dashboard.show(); return app.exec()

if __name__ == "__main__": raise SystemExit(main())
