# ui/main_window.py
# Main application window with app list and settings

import psutil
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QListView, QPushButton, QMessageBox, QCheckBox,
                             QGroupBox)
from PyQt5.QtCore import Qt, QTimer, QSortFilterProxyModel
from models import AppListModel
from monitors import ProcessMonitor
from ui.focus_popup import AimfulnessPopup
from utils.autostart import is_autostart_enabled, toggle_autostart
from config import BREAK_DURATION_SECONDS


class MainWindow(QMainWindow):
    """Main application window for Aimfulness."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aimfulness")
        self.setGeometry(100, 100, 600, 400)

        # Data model for application list
        self.model = AppListModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        # Process monitoring thread
        self.monitor = ProcessMonitor()
        self.monitor.app_detected.connect(self.on_app_detected)

        # Active breaks: {app_name: {'timer': QTimer, 'exec_path': str}}
        self.active_breaks = {}

        # Load data and start monitoring
        self.model.load_apps()
        self.model.load_state()
        self.update_monitor_list()
        self.monitor.start()

        # Build UI
        self.setup_ui()

    def setup_ui(self):
        """Create and arrange all UI elements."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Application list view
        self.list_view = QListView()
        self.list_view.setModel(self.proxy_model)
        layout.addWidget(self.list_view)

        # Control buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.refresh_apps)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

        # Autostart section
        autostart_group = QGroupBox("Autostart")
        autostart_layout = QHBoxLayout()
        self.autostart_cb = QCheckBox("Launch at system startup")
        self.autostart_cb.stateChanged.connect(self.on_autostart_toggled)
        autostart_layout.addWidget(self.autostart_cb)
        autostart_group.setLayout(autostart_layout)
        layout.addWidget(autostart_group)

        # Set initial autostart checkbox state
        self.autostart_cb.setChecked(is_autostart_enabled())

    def update_monitor_list(self):
        """Update the monitor with currently checked applications."""
        apps = self.model.get_checked_apps()
        self.monitor.update_blocked_list(apps)

    def save_settings(self):
        """Save current checkbox state to disk and update monitor."""
        self.model.save_state()
        self.update_monitor_list()
        QMessageBox.information(self, "Success", "Settings saved!")

    def refresh_apps(self):
        """
        Reload application list from .desktop files.
        Preserves existing checkbox states where possible.
        """
        # Remember old checked apps to restore them
        old_checked = self.model.get_checked_apps()
        
        self.model.load_apps()
        
        # Restore checkbox states by exec_path
        for item in self.model._items:
            if (item.exec_path, item.name) in old_checked:
                item.is_checked = True
                
        self.model._sort_items()
        self.model.dataChanged.emit(self.model.index(0),
                                    self.model.index(self.model.rowCount() - 1),
                                    [Qt.CheckStateRole])
        self.model.save_state()
        self.update_monitor_list()
        QMessageBox.information(self, "Done", "Application list updated!")

    def on_app_detected(self, app_name, exec_path, pid):
        """
        Handle detection of a blocked application.
        Shows popup only if app is not already in break mode.
        """
        if app_name in self.active_breaks:
            return  # App is in break mode, let it run
            
        popup = AimfulnessPopup(app_name, exec_path, pid)
        popup.kill_now.connect(self.kill_process_now)
        popup.break_requested.connect(self.start_break)
        popup.show()

    def kill_process_now(self, app_name, pid):
        """Terminate a process immediately by its PID."""
        try:
            proc = psutil.Process(int(pid))
            proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass  # Process already gone or can't be terminated

    def start_break(self, app_name, exec_path):
        """
        Start a break for the specified application.
        During break, the app won't trigger popups.
        After break duration, all instances are terminated.
        """
        if app_name in self.active_breaks:
            return
            
        # Register break in monitor
        self.monitor.add_break(app_name)
        
        # Create single-shot timer
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.end_break(app_name, exec_path))
        timer.start(BREAK_DURATION_SECONDS * 1000)
        
        self.active_breaks[app_name] = {'timer': timer, 'exec_path': exec_path}

    def end_break(self, app_name, exec_path):
        """
        End the break: terminate all instances of the application
        and clean up break-related data.
        """
        # Kill all processes with this executable path
        for proc in psutil.process_iter(['exe']):
            try:
                if proc.info['exe'] == exec_path:
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        # Clean up monitor and local storage
        self.monitor.remove_break(app_name)
        self.active_breaks.pop(app_name, None)

    def on_autostart_toggled(self, state):
        """Enable or disable autostart based on checkbox state."""
        enable = (state == Qt.Checked)
        toggle_autostart(enable)

    def closeEvent(self, event):
        """Clean up before closing the application."""
        self.monitor.stop()
        event.accept()