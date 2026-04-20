# utils/autostart.py
# Functions for managing application autostart on Linux

import os
import sys
from pathlib import Path
from config import AUTOSTART_DIR, AUTOSTART_FILENAME


def is_autostart_enabled() -> bool:
    """
    Check if Aimfulness is configured to launch at system startup.
    Returns True if .desktop file exists in user's autostart directory.
    """
    desktop_file = AUTOSTART_DIR / AUTOSTART_FILENAME
    return desktop_file.exists()


def toggle_autostart(enable: bool):
    """
    Enable or disable autostart by creating/removing a .desktop file.
    
    Args:
        enable: True to enable autostart, False to disable
    """
    AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
    desktop_file = AUTOSTART_DIR / AUTOSTART_FILENAME

    if enable:
        # Path to current Python interpreter and script
        exec_path = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        
        content = f"""[Desktop Entry]
            Type=Application
            Name=Aimfulness
            Exec={exec_path} {script_path}
            Hidden=false
            NoDisplay=false
            X-GNOME-Autostart-enabled=true
            """
        with open(desktop_file, 'w') as f:
            f.write(content)
        os.chmod(desktop_file, 0o755)  # Make executable
    else:
        if desktop_file.exists():
            desktop_file.unlink()