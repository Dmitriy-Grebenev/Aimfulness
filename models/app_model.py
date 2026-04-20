# models/app_model.py
# Data model for application list with checkbox state and sorting

import json
from pathlib import Path
from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex
from config import DESKTOP_DIRS, CHECKED_APPS_FILE


class AppItem:
    """Storage class for application information."""
    def __init__(self, name: str, exec_path: str = ""):
        self.name = name          # Display name
        self.exec_path = exec_path # Path to executable
        self.is_checked = False   # Checkbox state

    def __repr__(self):
        return f"AppItem({self.name}, {self.exec_path}, {self.is_checked})"


class AppListModel(QAbstractListModel):
    """
    List model for applications with checked items sorted to the top.
    Loads applications from .desktop files and persists checkbox state.
    """
    def __init__(self):
        super().__init__()
        self._items = []          # All items (original unsorted)
        self._sorted_items = []   # Sorted items for display

    def load_apps(self):
        """Load applications from .desktop files in standard directories."""
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
                        exec_path = None
                        no_display = False
                        
                        for line in lines:
                            line = line.strip()
                            if line.startswith("Name=") and name is None:
                                name = line[5:].strip()
                            elif line.startswith("Exec="):
                                exec_path = line[5:].split()[0].strip()
                            elif line == "NoDisplay=true":
                                no_display = True
                                break
                                
                        if name and exec_path and not no_display:
                            # Skip shells and system utilities that would clutter the list
                            if any(exclude in exec_path for exclude in
                                   ["/usr/bin/env", "/bin/sh", "/bin/bash", "python"]):
                                continue
                            self._items.append(AppItem(name, exec_path))
                except Exception:
                    continue  # Skip malformed .desktop files
                    
        self._items.sort(key=lambda x: x.name)
        self._sort_items()
        self.endResetModel()

    def _sort_items(self):
        """Sort items: checked items first, then alphabetically by name."""
        checked = [item for item in self._items if item.is_checked]
        unchecked = [item for item in self._items if not item.is_checked]
        checked.sort(key=lambda x: x.name)
        unchecked.sort(key=lambda x: x.name)
        self._sorted_items = checked + unchecked

    def data(self, index, role=Qt.DisplayRole):
        """Return data for a given index and role."""
        if not index.isValid():
            return None
            
        item = self._sorted_items[index.row()]
        
        if role == Qt.DisplayRole:
            return item.name
        elif role == Qt.CheckStateRole:
            return Qt.Checked if item.is_checked else Qt.Unchecked
            
        return None

    def setData(self, index, value, role=Qt.EditRole):
        """Set checkbox state when user toggles it."""
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
            return True
        return False

    def flags(self, index):
        """Make items checkable."""
        return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled

    def rowCount(self, parent=QModelIndex()):
        """Return number of items in the model."""
        return len(self._sorted_items)

    def get_checked_apps(self):
        """
        Return list of (exec_path, app_name) tuples for checked applications.
        Used by ProcessMonitor to know which apps to block.
        """
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
            pass  # No saved state yet, that's fine