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

# Directories to search for .desktop files (Linux only)
DESKTOP_DIRS = [
    "/usr/share/applications",
    str(Path.home() / ".local/share/applications")
]

# Global style for the application (dark theme, rounded buttons, teal checkboxes)
APP_STYLE = """
QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: "Cascadia Code", "Courier New", monospace;
    font-size: 14pt;
    border-radius: 10px;
}

QListView {
    background-color: #252526;
    alternate-background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 8px;
    outline: none;
}

QListView::item {
    padding: 8px;
    border-bottom: 1px solid #3c3c3c;
    border-radius: 5px;
}

QListView::item:selected {
    background-color: #094771;
}

QCheckBox {
    spacing: 28px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #4ec9b0;
    background-color: #252526;
}

QCheckBox::indicator:checked {
    background-color: #4ec9b0;
    border: 2px solid #4ec9b0;
    image: url(none);
}

QPushButton {
    background-color: #0e639c;
    border: none;
    border-radius: 10px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1177bb;
}

QPushButton:pressed {
    background-color: #0a4f7a;
}

QGroupBox {
    border: 1px solid #3c3c3c;
    border-radius: 10px;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
"""

# Style for popup window 
POPUP_STYLE = """
QWidget {
    background-color: #1e1e1e;           
    color: #d4d4d4;                       
    font-family: "Cascadia Code", "Courier New", monospace;
    font-size: 14pt;
    border-radius: 12px;
}

QLabel {
    color: #d4d4d4;
    font-size: 14pt;
    qproperty-alignment: AlignCenter;
    margin: 10px;
}

QPushButton {
    background-color: #0e639c;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 24px;                  
    font-weight: bold;
    min-width: 120px;                    
}

QPushButton:hover {
    background-color: #1177bb;
}

QPushButton:pressed {
    background-color: #0a4f7a;
}

/* Отступы между кнопками */
QHBoxLayout {
    spacing: 12px;
}
"""