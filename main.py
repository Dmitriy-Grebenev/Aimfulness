#!/usr/bin/env python3
# main.py
# Entry point for Aimfulness application

import sys
from PyQt5.QtWidgets import QApplication
from ui import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())