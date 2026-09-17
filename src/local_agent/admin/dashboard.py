"""Administrator-only PySide6 dashboard for Sentinel."""
import sys
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QFormLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from sqlalchemy import select

from src.local_agent.database.connection import SessionLocal
from src.local_agent.database.models import AuditLog, Evidence, RiskEvent, SecurityEvent, Session
from src.local_agent.security.access_control import AccessController
from src.local_agent.security.encryption import EncryptionManager


class Login(QDialog):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Sentinel Administrator Authentication")
        self.username, self.password = QLineEdit(), QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        button = QPushButton("Authenticate"); button.clicked.connect(self.login)
        form = QFormLayout(self); form.addRow("Username", self.username); form.addRow("Sentinel password", self.password); form.addRow(button)
        self.admin_id = None
    def login(self):
        result = AccessController().authorize_admin_dashboard(self.username.text().strip(), self.password.text())
        if result.allowed:
            self.admin_id = result.user_id; self.accept()
        else: QMessageBox.warning(self, "Access denied", result.message)


class Dashboard(QMainWindow):
    def __init__(self, admin_id):
        super().__init__(); self.admin_id = admin_id; self.setWindowTitle("Sentinel Administrator Dashboard"); self.resize(1100, 700)
        self.tabs = QTabWidget(); self.setCentralWidget(self.tabs)
        self.summary = QLabel(); self.summary.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.risks = self.table(["Time", "Session", "Score", "Level", "Response"])
        self.sessions = self.table(["ID", "User", "Started", "Ended", "State"])
        self.alerts = self.table(["Time", "Session", "Severity", "Event", "State"])
        self.photos = self.table(["ID", "Time", "Session", "Risk event", "Expires"])
        for name, widget in (("Overview & trends", self.summary), ("Risk scores", self.risks), ("Sessions", self.sessions), ("Alerts & logs", self.alerts), ("Captured photos", self.photos)):
            page = QWidget(); layout = QVBoxLayout(page); layout.addWidget(widget); self.tabs.addTab(page, name)
        view = QPushButton("View selected encrypted photo"); view.clicked.connect(self.view_photo)
        self.tabs.widget(4).layout().addWidget(view); self.tabs.currentChanged.connect(lambda _: self.refresh()); self.refresh()
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
            db.add(AuditLog(admin_id=self.admin_id, timestamp=datetime.utcnow(), action="VIEW_DASHBOARD", resource_type="DASHBOARD")); db.commit()
        self.summary.setText(f"Current security overview\n\nRecent risk decisions: {len(risks)}\nHigh risk: {sum(x.risk_level == 'HIGH' for x in risks)}\nCritical risk: {sum(x.risk_level == 'CRITICAL' for x in risks)}\nOpen alerts: {sum(x.status == 'OPEN' for x in alerts)}\n\nUse Risk scores for history and behavioural trends.")
        self.fill(self.risks, [[x.timestamp,x.session_id,x.risk_score,x.risk_level,x.response] for x in risks]); self.fill(self.sessions, [[x.id,x.user_id,x.started_at,x.ended_at,x.status] for x in sessions]); self.fill(self.alerts, [[x.timestamp,x.session_id,x.severity,x.event_type,x.status] for x in alerts]); self.fill(self.photos, [[x.id,x.timestamp,x.session_id,x.risk_event_id,x.expires_at] for x in photos])
    def view_photo(self):
        row = self.photos.currentRow()
        if row < 0: return QMessageBox.information(self, "Sentinel", "Select evidence first.")
        evidence_id = int(self.photos.item(row, 0).text())
        with SessionLocal() as db:
            evidence = db.get(Evidence, evidence_id)
            try:
                with open(evidence.file_reference, "rb") as source: image = EncryptionManager().decrypt_data(source.read())
            except (FileNotFoundError, ValueError) as error: return QMessageBox.warning(self, "Evidence unavailable", str(error))
            db.add(AuditLog(admin_id=self.admin_id, timestamp=datetime.utcnow(), action="VIEW_EVIDENCE", resource_type="EVIDENCE", resource_id=str(evidence_id))); db.commit()
        pixmap = QPixmap(); pixmap.loadFromData(image); label = QLabel(); label.setPixmap(pixmap.scaled(900,650,Qt.AspectRatioMode.KeepAspectRatio)); dialog = QDialog(self); dialog.setWindowTitle(f"Evidence {evidence_id}"); layout = QVBoxLayout(dialog); layout.addWidget(label); dialog.exec()


def main():
    app = QApplication(sys.argv); login = Login()
    if login.exec() != QDialog.DialogCode.Accepted: return 1
    dashboard = Dashboard(login.admin_id); dashboard.show(); return app.exec()

if __name__ == "__main__": raise SystemExit(main())
