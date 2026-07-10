#!/bin/bash
echo "Installing Bangla Dictation dependencies..."

# Install required system packages
sudo apt-get update
sudo apt-get install -y wl-clipboard ydotool python3-pip python3-venv ffmpeg

echo "Adding user to input group for evdev..."
sudo usermod -aG input $USER

echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "    Bangla Dictation & API Setup"
echo "=========================================="
echo "Please select your preferred running mode:"
echo "1) Full Experience (Global Dictation Hotkeys + Background API Server)"
echo "2) API Server Only (No background dictation hotkeys, lower RAM usage)"
read -p "Select option (1 or 2): " mode_choice

# Default to 1 if invalid
if [[ "$mode_choice" != "1" && "$mode_choice" != "2" ]]; then
    mode_choice="1"
fi

cat <<EOF > config.json
{
  "mode": "$mode_choice",
  "language": "bn-BD",
  "websocket_port": 8765
}
EOF

echo "Configuration saved!"
echo ""
echo "Installation complete!"
echo ""
echo "IMPORTANT: Please log out and log back in so the 'input' group permissions take effect."
echo "To run the daemon, execute:"
echo "sg input -c './venv/bin/python app.py'"
