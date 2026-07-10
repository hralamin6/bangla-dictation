# Bangla Dictation (Linux Daemon)

A lightweight, headless background service for Ubuntu/Pop!_OS that enables global press-and-hold dictation. It uses a hidden instance of Google Chrome to process voice using the Web Speech API and injects the transcribed text directly into your active cursor using native Linux input events (`evdev` and `ydotool`).

## Features
- **Invisible**: Runs completely silently in the background with zero GUI overhead.
- **Wayland Native**: Fully compatible with Wayland (and X11) through raw `uinput` interception.
- **Dual Language**:
  - `Hold Right Ctrl` ➔ English Dictation (Types using `ydotool` without touching clipboard)
  - `Hold Right Ctrl + Right Alt` ➔ Bangla Dictation (Types using `wl-clipboard` and `evdev` to inject Unicode)
- **True Handy-style**: Starts listening instantly on key press, types the moment you release the keys.

## Installation

Run the installation script to grab dependencies and create the python virtual environment:
```bash
./install.sh
```

**Important**: You *must* add your user to the `input` group so the script can monitor hotkeys without root:
```bash
sudo usermod -aG input $USER
```
*Note: You must log out and log back in for this group change to take effect.*

## How to run (Manually)

Since the script needs `input` group permissions, if you haven't logged out yet, you can run it via `sg`:
```bash
sg input -c "./venv/bin/python app.py"
```
Or, if you have rebooted/logged back in, simply:
```bash
./venv/bin/python app.py
```

## How to run (Autostart on Boot)

To have the daemon automatically start silently in the background every time you turn on your computer:

1. Copy the systemd service to your user directory:
```bash
mkdir -p ~/.config/systemd/user/
cp bangla-dictation.service ~/.config/systemd/user/
```

2. Enable and start it:
```bash
systemctl --user daemon-reload
systemctl --user enable --now bangla-dictation.service
```

3. Check if it's running:
```bash
systemctl --user status bangla-dictation.service
```
