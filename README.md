# 🎯 Aimfulness

> A lightweight, distraction-blocking desktop application for Linux.  
> Detects blocked applications, prompts you to close them or take a timed break, and works seamlessly on both Wayland and X11.

---

## ✨ Features

- 🔍 **Real-time Monitoring**: Instantly detects when a blocked app launches.
- 🪟 **Focus Popup**: Clean, dark-themed overlay with two clear actions: *Close App* or *Take a 5-min Break*.
- ⏱️ **Smart Breaks**: Cooldown timer per app. Automatically resets when Focus Mode is toggled off/on.
-  **Instant Scan**: Checks for already running apps on startup and when re-enabling Focus Mode.
- 🖥️ **Wayland & X11 Ready**: Optimized for GNOME Wayland, with X11 fallback support.
- 🧠 **Event-Driven Core**: Clean Qt signal/slot architecture. Zero arbitrary delays, zero race conditions.

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- PyQt5
- psutil

### 1. Install System Dependencies
**Arch Linux / Manjaro:**
```bash
sudo pacman -S python-pyqt5 python-psutil
```

**Ubuntu / Debian:**
```bash
sudo apt install python3-pyqt5 python3-psutil
```

### 2. Clone & Setup
```bash
git clone https://github.com/Dmitriy-Grebenev/Aimfulness.git
cd Aimfulness
pip install -r requirements.txt  # Create this file if missing: pyqt5, psutil
```

---

## 🚀 Usage

### Run the Application
```bash
python main.py
```
> 💡 **Wayland Note**: Aimfulness runs natively on Wayland. If you encounter display issues, force the XCB backend:
> ```bash
> QT_QPA_PLATFORM=xcb python main.py
> ```

### How It Works
1. Click **Focus Mode** to enable monitoring.
2. Launch a blocked application (e.g., Calculator, Telegram, Games).
3. A popup appears instantly. Choose:
   - 🔴 **Close App** – Terminates the process immediately.
   - ⏸️ **Take a Break** – Pauses blocking for 5 minutes.
4. Toggle Focus Mode off/on to reset all active breaks and rescan running apps.

---

## ⚙️ Configuration

All settings are managed in `config.py`:

| Parameter | Description |
|-----------|-------------|
| `BLOCKED_APPS` | List of `(executable_path, "Display Name")` tuples to monitor. |
| `BREAK_DURATION_SECONDS` | Duration of the break cooldown (default: `300` = 5 min). |
| `APP_STYLE` / `POPUP_STYLE` | Qt stylesheets for the main window and popup. |

**Adding Apps:**
Find the executable path:
```bash
which gnome-calculator  # Output: /usr/bin/gnome-calculator
```
Add to `BLOCKED_APPS` in `config.py`:
```python
BLOCKED_APPS = [
    ('/usr/bin/gnome-calculator', 'Calculator'),
    ('/usr/bin/telegram-desktop', 'Telegram'),
    # Add more...
]
```

---

## 🛠️ Technical Details

- **Process Monitoring**: Runs in a dedicated `QThread` using `psutil`. Normalizes paths via `os.path.realpath()` to handle symlinks, Flatpak, and sandboxes correctly.
- **Event-Driven UI**: Uses Qt signals/slots (`QueuedConnection`) for thread-safe communication. Zero `time.sleep()` or arbitrary delays.
- **Wayland Compatibility**: Uses `Qt.Tool | Qt.WindowStaysOnTopHint` and `QTimer.singleShot(0, raise_)` to correctly handle window stacking and focus on Wayland compositors.
- **State Management**: Break timers and active app states are stored in `self.active_breaks`. Automatically cleared on Focus Mode toggle to prevent state leakage.
- **Zero-Crash Design**: Handles `psutil.NoSuchProcess` and `AccessDenied` gracefully. Zombie processes and sandboxed apps are safely ignored.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs or suggest features via [Issues](https://github.com/Dmitriy-Grebenev/Aimfulness/issues)
- Submit PRs for UI improvements, new integrations, or performance tweaks
- Test on different DEs/Wayland compositors and share feedback

---

## 📜 License

Distributed under the [MIT License](LICENSE).

---
*Made with ❤️ for focused workflows on Linux.*