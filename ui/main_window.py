# ui/main_window.py
# Main application window with app list, global switch, and autostart

import psutil
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QListView, QPushButton, QMessageBox, QCheckBox,
                             QGroupBox, QApplication)
from PyQt5.QtCore import Qt, QTimer, QSortFilterProxyModel
from models import AppListModel
from monitors import ProcessMonitor
from ui.focus_popup import AimfulnessPopup
from utils.autostart import is_autostart_enabled, toggle_autostart
from config import BREAK_DURATION_SECONDS, APP_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aimfulness")
        self.setGeometry(100, 100, 650, 500)

        # Apply global dark theme
        self.setStyleSheet(APP_STYLE)

        # Data model
        self.model = AppListModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        # Process monitor
        self.monitor = ProcessMonitor()

        self.monitor.app_detected.connect(
            self.on_app_detected,
            type=Qt.QueuedConnection
        )

        print(f"[DEBUG] Signal connected")

        # Active breaks storage
        self.active_breaks = {}

        # Global focus mode enabled flag
        self.focus_mode_enabled = True

        # Load apps and state, start monitor
        self.model.load_apps()
        self.model.load_state()
        self.update_monitor_list()
        self.monitor.start()

        print("[DEBUG] Monitor thread is running:", self.monitor.isRunning())

        # Scan for apps
        QTimer.singleShot(1000, self.scan_for_existing_apps)

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Global focus mode toggle
        self.focus_toggle = QCheckBox("Focus Mode (block selected apps)")
        self.focus_toggle.setChecked(True)
        self.focus_toggle.setStyleSheet("font-weight: bold; color: #4ec9b0;")
        self.focus_toggle.toggled.connect(self.toggle_focus_mode)
        layout.addWidget(self.focus_toggle)

        # Application list
        self.list_view = QListView()
        self.list_view.setModel(self.proxy_model)
        layout.addWidget(self.list_view)

        # Refresh button (only manual refresh, no save button)
        refresh_btn = QPushButton("Refresh Application List")
        refresh_btn.clicked.connect(self.refresh_apps)
        layout.addWidget(refresh_btn)

        # Autostart section
        autostart_group = QGroupBox("Autostart")
        autostart_layout = QHBoxLayout()
        self.autostart_cb = QCheckBox("Launch Aimfulness at system startup")
        self.autostart_cb.stateChanged.connect(self.on_autostart_toggled)
        autostart_layout.addWidget(self.autostart_cb)
        autostart_group.setLayout(autostart_layout)
        layout.addWidget(autostart_group)

        # Set autostart checkbox state
        self.autostart_cb.setChecked(is_autostart_enabled())

    def toggle_focus_mode(self, enabled):
        """Enable or disable the entire blocking mechanism."""
        self.focus_mode_enabled = enabled
        
        if not enabled:
            print("[DEBUG] Focus Mode DISABLED. Cleaning up...")
            
            # Stop all timers
            for app_name, info in self.active_breaks.items():
                timer = info.get('timer')
                if timer and timer.isActive():
                    timer.stop()
                    print(f"   Stopped timer for {app_name}")
            
            # Clear breaks
            self.active_breaks.clear()
            
            # Clear in monitor
            if hasattr(self.monitor, 'clear_breaks'):
                self.monitor.clear_breaks()
            
            print("[DEBUG] All timers stopped and break lists cleared.")
            
        else:
            print("[DEBUG] Focus Mode ENABLED. Starting monitor...")
            self.monitor.start()
            
            # Scan already opened apps
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, self.scan_for_existing_apps)
            # 1 second delay for monitor to be opened in time 

    def update_monitor_list(self):
        """Update the monitor's blocked list based on current selections."""
        if self.focus_mode_enabled:
            apps = self.model.get_checked_apps()
            self.monitor.update_blocked_list(apps)

            print("[DEBUG] Updating monitor with apps:", apps)
        else:
            self.monitor.update_blocked_list([])
        
    def refresh_apps(self):
        """Reload application list from .desktop files, preserving checked state."""
        old_checked = self.model.get_checked_apps()
        self.model.load_apps()
        # Restore checkboxes
        for item in self.model._items:
            if (item.exec_path, item.name) in old_checked:
                item.is_checked = True
        self.model._sort_items()
        self.model.dataChanged.emit(self.model.index(0),
                                    self.model.index(self.model.rowCount() - 1),
                                    [Qt.CheckStateRole])
        self.model.save_state()
        self.update_monitor_list()
        QMessageBox.information(self, "Done", "Application list refreshed!")

    def on_app_detected(self, app_name, exec_path, pid):
        """Handle detection of a blocked application."""
        print(f"[DEBUG] on_app_detected: app={app_name}, path={exec_path}, pid={pid}")
        if not self.focus_mode_enabled:
            print("[DEBUG] Focus mode disabled, ignoring")
            return
        if app_name in self.active_breaks:
            print(f"[DEBUG] {app_name} is in active_breaks, ignoring")
            return

        try:
            print("[DEBUG] Creating AimfulnessPopup...")
            # saving to self for not deleting by GC
            self.current_popup = AimfulnessPopup(app_name, exec_path, pid)
            
            print("[DEBUG] Popup created, connecting signals...")
            self.current_popup.kill_now.connect(self.kill_process_now)
            self.current_popup.break_requested.connect(self.start_break)
            
            print("[DEBUG] Signals connected, calling popup.show()...")
            self.current_popup.show()
            
            # for Wayland: wait before raixe_() 
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(50, lambda: [
                self.current_popup.raise_(),
                self.current_popup.activateWindow()
            ])
            
            print("[DEBUG] popup.show() returned")
            
        except Exception as e:
            print(f"[ERROR] Exception in on_app_detected: {e}")
            import traceback
            traceback.print_exc()

    def scan_for_existing_apps(self):
        """Scan for already running blocked applications."""
        print("[DEBUG] Scanning for existing blocked apps...")
        
        blocked_apps = self.monitor.blocked_apps  # dict {path: name}
        
        import psutil
        
        for proc in psutil.process_iter(['pid', 'exe', 'name']):
            try:
                proc_exe = proc.info['exe']
                if not proc_exe:
                    continue
                
                # Normalizing path (as in monitor)
                import os
                try:
                    proc_exe = os.path.realpath(proc_exe)
                except:
                    pass
                
                # Check if process in blocked
                if proc_exe in blocked_apps:
                    app_name = blocked_apps[proc_exe]
                    
                    # Do not show if already in break
                    if app_name in self.active_breaks:
                        continue
                    
                    print(f"[DEBUG] Found existing blocked app: {app_name} (PID: {proc.info['pid']})")
                    
                    # Show popup with little delay
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(
                        500,  # 500 ms between popups
                        lambda name=app_name, exe=proc_exe, pid=str(proc.info['pid']): 
                            self.on_app_detected(name, exe, pid)
                    )
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print("[DEBUG] Scan completed.")

    def kill_process_now(self, app_name, pid):
        """Terminate a process immediately."""
        try:
            proc = psutil.Process(int(pid))
            proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def start_break(self, app_name, exec_path):
        """Start a 5-minute break for the application."""
        if app_name in self.active_breaks:
            return
        self.monitor.add_break(app_name)

        timer = QTimer()
        timer.setSingleShot(True)
        
        timer.timeout.connect(lambda: self.end_break(app_name, exec_path))
        timer.start(BREAK_DURATION_SECONDS * 1000)
        self.active_breaks[app_name] = {'timer': timer, 'exec_path': exec_path}

    def end_break(self, app_name, exec_path):
        """End the break: kill all instances and clean up."""
        for proc in psutil.process_iter(['exe']):
            try:
                if proc.info['exe'] == exec_path:
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        self.monitor.remove_break(app_name)
        self.active_breaks.pop(app_name, None)

    def on_autostart_toggled(self, state):
        enable = (state == Qt.Checked)
        toggle_autostart(enable)

    def closeEvent(self, event):
        self.monitor.stop()
        event.accept()

