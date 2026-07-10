import os
import sys
import json
import asyncio
import threading
from server import start_server
from hotkey import setup_hotkeys
from browser import launch_browser
from logger import setup_logger

logger = setup_logger()

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def main():
    logger.info("Starting Bangla Dictation Daemon...")
    config = load_config()

    # Start WebSocket server
    loop = asyncio.new_event_loop()
    server_thread = threading.Thread(target=start_server, args=(loop, config), daemon=True)
    server_thread.start()
    
    # Setup Hotkeys
    setup_hotkeys(config, loop)
    
    # Launch Browser
    launch_browser(config)
    
    logger.info("Application is running silently in the background.")
    try:
        # Keep the main thread alive indefinitely
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Exiting...")
        loop.call_soon_threadsafe(loop.stop)
        server_thread.join(timeout=2)

if __name__ == '__main__':
    main()
