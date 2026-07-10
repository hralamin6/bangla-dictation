#!/bin/bash
echo "Installing Bangla Dictation dependencies..."

# Install required system packages
sudo apt-get update
sudo apt-get install -y wl-clipboard ydotool python3-pip python3-venv

echo "Adding user to input group for evdev..."
sudo usermod -aG input $USER

echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "Installation complete!"
echo ""
echo "IMPORTANT: Please log out and log back in so the 'input' group permissions take effect."
echo "To run the daemon, execute:"
echo "sg input -c './venv/bin/python app.py'"
