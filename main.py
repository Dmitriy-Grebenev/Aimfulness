#!/usr/bin/env python3
# main.py
# Entry point for Aimfulness

import os
os.environ["QT_QPA_PLATFORM"] = "xcb"  # явно принудительно
print("QT_QPA_PLATFORM set to:", os.environ.get("QT_QPA_PLATFORM"))

import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

if __name__ == "__main__":
    import os
    if "WAYLAND_DISPLAY" in os.environ and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())