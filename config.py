# config.py
# Configuration constants for Aimfulness

import os
from pathlib import Path

# File to store selected applications (JSON format)
CHECKED_APPS_FILE = "checked_apps.json"

# Break duration in seconds (5 minutes by default)
BREAK_DURATION_SECONDS = 5 * 60

# Autostart file name
AUTOSTART_FILENAME = "aimfulness.desktop"

# User's autostart directory
AUTOSTART_DIR = Path.home() / ".config/autostart"

# Directories to search for .desktop files
DESKTOP_DIRS = [
    "/usr/share/applications",
    str(Path.home() / ".local/share/applications")
]

# CSS style for popup window
POPUP_STYLE = """
    QWidget {
        background-color: #2c2c2c;
        color: #eee;
        border-radius: 8px;
        border: 1px solid #555;
    }
    QPushButton {
        background-color: #3c3c3c;
        padding: 6px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #5c5c5c;
    }
"""