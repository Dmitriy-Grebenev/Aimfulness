# ui/focus_popup.py
# Popup window that appears when a blocked application is launched

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from config import POPUP_STYLE


class AimfulnessPopup(QWidget):
    """
    Small popup window that asks user what to do with the blocked application.
    Provides two options: close now or allow a 5-minute break.
    """
    kill_now = pyqtSignal(str, str)       # (app_name, pid)
    break_requested = pyqtSignal(str, str) # (app_name, exec_path)

    def __init__(self, app_name, exec_path, pid):
        super().__init__()
        self.app_name = app_name
        self.exec_path = exec_path
        self.pid = pid
        self.setWindowTitle("Aimfulness")
        
        #self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        self.setWindowFlags(
            Qt.Tool | 
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint
        )

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # No modal – just stays on top
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel(f"Distracting application detected:\n{self.app_name}")
        label.setStyleSheet("font-size: 14pt;")
        layout.addWidget(label)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.on_ok)
        break_btn = QPushButton("Take a break (5 min)")
        break_btn.clicked.connect(self.on_break)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(break_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.setStyleSheet(POPUP_STYLE)
        self.adjustSize()

    def on_ok(self):
        self.kill_now.emit(self.app_name, self.pid)
        self.close()

    def on_break(self):
        self.break_requested.emit(self.app_name, self.exec_path)
        self.close()

    def showEvent(self, event):
        print(f"[DEBUG POPUP] showEvent called, geometry: {self.geometry().getRect()}")
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.center() - self.rect().center(),
        )
        super().showEvent(event)