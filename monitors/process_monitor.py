# monitors/process_monitor.py
# Background thread that monitors for blocked application launches

import psutil
from PyQt5.QtCore import QThread, pyqtSignal


class ProcessMonitor(QThread):
    """
    Background thread that continuously checks for newly launched processes.
    Emits a signal when a blocked application is detected.
    """
    # Signal emitted when a blocked app is launched: (app_name, exec_path, pid)
    app_detected = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.blocked_apps = {}      # {exec_path: app_name}
        self.break_apps = set()     # App names currently in break mode
        self.running = True

    def update_blocked_list(self, apps):
        """
        Update the list of applications to monitor.
        apps: list of tuples (exec_path, app_name)
        """
        self.blocked_apps = dict(apps)

    def add_break(self, app_name):
        """
        Add an application to break mode.
        While in break mode, this app won't trigger popups.
        """
        self.break_apps.add(app_name)

    def remove_break(self, app_name):
        """Remove an application from break mode."""
        self.break_apps.discard(app_name)

    def run(self):
        """Main monitoring loop. Runs in a separate thread."""
        # Get initial set of PIDs to avoid false positives for already running apps
        known_pids = set(psutil.pids())
        
        while self.running:
            current_pids = set(psutil.pids())
            new_pids = current_pids - known_pids
            
            for pid in new_pids:
                try:
                    proc = psutil.Process(pid)
                    proc_exe = proc.exe()
                    
                    if proc_exe in self.blocked_apps:
                        app_name = self.blocked_apps[proc_exe]
                        # Only trigger if app is not in break mode
                        if app_name not in self.break_apps:
                            self.app_detected.emit(app_name, proc_exe, str(pid))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass  # Process already terminated or insufficient permissions
                    
            known_pids = current_pids
            self.msleep(1000)  # Check once per second

    def stop(self):
        """Stop the monitoring thread gracefully."""
        self.running = False
        self.quit()
        self.wait()