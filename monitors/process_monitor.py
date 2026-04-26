# monitors/process_monitor.py
# Background thread that monitors for blocked application launches

import psutil
from PyQt5.QtCore import QThread, pyqtSignal

import os

def normalize_path(path):
    """Make path canonical"""
    try:
        return os.path.realpath(path)
    except:
        return path



class ProcessMonitor(QThread):
    """
    Background thread that continuously checks for newly launched processes.
    Emits a signal when a blocked application is detected.
    """
    app_detected = pyqtSignal(str, str, str)  # (app_name, exec_path, pid)

    def __init__(self):
        super().__init__()
        self.blocked_apps = {}      # {exec_path: app_name}
        self.break_apps = set()     # App names currently in break mode
        self.running = True
        self.known_pids = set()     # Track known PIDs

    def update_blocked_list(self, apps):
        """
        Update the list of applications to monitor.
        apps: list of tuples (exec_path, app_name)
        """
        self.blocked_apps = {normalize_path(path): name for path, name in apps}
        # Refresh known PIDs when blocked list changes
        self.known_pids = set(psutil.pids())

    def clear_breaks(self):
        """Clears all apps currently on break so they can be detected again."""
        self.break_apps.clear()
        print("[DEBUG MON] Break apps cleared.")

    def add_break(self, app_name):
        """Add an application to break mode (won't trigger popups)."""
        self.break_apps.add(app_name)

    def remove_break(self, app_name):
        """Remove an application from break mode."""
        self.break_apps.discard(app_name)

    def run(self):
        """Main monitoring loop."""

        print("[DEBUG] ProcessMonitor thread started")

        self.known_pids = set(psutil.pids())
        
        print(f"[DEBUG MON] Initial known PIDs count: {len(self.known_pids)}")
        print(f"[DEBUG MON] Blocked apps at start: {self.blocked_apps}")
        while self.running:
            current_pids = set(psutil.pids())
            new_pids = current_pids - self.known_pids
            
            # DEBUG
            if new_pids:
                print(f"[DEBUG] New PIDs: {new_pids}")
                for pid in new_pids:
                    try:
                        proc = psutil.Process(pid)
                        print(f"  PID {pid}: exe={proc.exe()}, name={proc.name()}")
                    except Exception as e:
                        print(f"  Error: {e}")
            # END OF DEBUG

            for pid in new_pids:
                try:
                    proc = psutil.Process(pid)
                    proc_exe = proc.exe()

                    proc_exe = normalize_path(proc_exe)
                    
                    if proc_exe in self.blocked_apps:
                        app_name = self.blocked_apps[proc_exe]
                        if app_name not in self.break_apps:
                            print(f"[DEBUG MON] MATCH! Emitting signal for {app_name}")
                            self.app_detected.emit(app_name, proc_exe, str(pid))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            self.known_pids = current_pids
            self.msleep(500)  # Check twice per second

    def stop(self):
        """Stop the monitoring thread."""
        self.running = False
        self.quit()
        self.wait()