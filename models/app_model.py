# models/app_model.py
# Data model for application list with checkbox state and sorting

import json
import shutil
from pathlib import Path
from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex
from config import DESKTOP_DIRS, CHECKED_APPS_FILE


class AppItem:
    """Storage class for application information."""
    def __init__(self, name: str, exec_path: str = ""):
        self.name = name
        self.exec_path = exec_path  # Full resolved path or command name
        self.is_checked = False

    def __repr__(self):
        return f"AppItem({self.name}, {self.exec_path}, {self.is_checked})"


class AppListModel(QAbstractListModel):
    """
    List model for applications with checked items sorted to the top.
    Loads applications from .desktop files and persists checkbox state.
    Changes are saved immediately.
    """
    def __init__(self):
        super().__init__()
        self._items = []          # All items (original unsorted)
        self._sorted_items = []   # Sorted items for display

    def load_apps(self):
        """Load applications from .desktop files and resolve full executable paths."""
        self.beginResetModel()
        self._items = []
        for app_dir in DESKTOP_DIRS:
            desktop_dir = Path(app_dir)
            if not desktop_dir.exists():
                continue
            for desktop_file in desktop_dir.glob("*.desktop"):
                try:
                    with open(desktop_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        name = None
                        exec_cmd = None
                        no_display = False
                        for line in lines:
                            line = line.strip()
                            if line.startswith("Name=") and name is None:
                                name = line[5:].strip()
                            elif line.startswith("Exec="):
                                exec_cmd = line[5:].split()[0].strip()
                            elif line == "NoDisplay=true":
                                no_display = True
                                break
                        if name and exec_cmd and not no_display:
                            # Resolve full path using shutil.which
                            full_path = shutil.which(exec_cmd)
                            if full_path is None:
                                # If not found in PATH, keep as is (may still work)
                                full_path = exec_cmd
                            # Skip obvious shells and system utilities
                            if any(exclude in full_path for exclude in
                                   ["/usr/bin/env", "/bin/sh", "/bin/bash", "python"]):
                                continue
                            self._items.append(AppItem(name, full_path))
                except Exception:
                    continue
        self._items.sort(key=lambda x: x.name)
        self._sort_items()
        self.endResetModel()

    def _sort_items(self):
        """Sort items: checked first, then alphabetically."""
        checked = [item for item in self._items if item.is_checked]
        unchecked = [item for item in self._items if not item.is_checked]
        checked.sort(key=lambda x: x.name)
        unchecked.sort(key=lambda x: x.name)
        self._sorted_items = checked + unchecked

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        item = self._sorted_items[index.row()]
        if role == Qt.DisplayRole:
            return item.name
        elif role == Qt.CheckStateRole:
            return Qt.Checked if item.is_checked else Qt.Unchecked
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole and index.isValid():
            item = self._sorted_items[index.row()]
            # Find and update the original item
            for orig in self._items:
                if orig.name == item.name and orig.exec_path == item.exec_path:
                    orig.is_checked = (value == Qt.Checked)
                    break
            self._sort_items()
            self.dataChanged.emit(self.index(0), self.index(self.rowCount() - 1),
                                  [Qt.CheckStateRole])
            # Auto-save whenever checkbox changes
            self.save_state()
            return True
        return False

    def flags(self, index):
        return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled

    def rowCount(self, parent=QModelIndex()):
        return len(self._sorted_items)

    def get_checked_apps(self):
        """Return list of (exec_path, app_name) for checked applications."""
        return [(item.exec_path, item.name) for item in self._items if item.is_checked]

    def save_state(self, filename=CHECKED_APPS_FILE):
        """Save checked application names to JSON file."""
        checked_names = [item.name for item in self._items if item.is_checked]
        with open(filename, 'w') as f:
            json.dump(checked_names, f)

    def load_state(self, filename=CHECKED_APPS_FILE):
        """Load checked application names from JSON file."""
        try:
            with open(filename, 'r') as f:
                checked_names = json.load(f)
            for item in self._items:
                item.is_checked = item.name in checked_names
            self._sort_items()
            self.dataChanged.emit(self.index(0), self.index(self.rowCount() - 1),
                                  [Qt.CheckStateRole])
        except FileNotFoundError:
            pass