import subprocess
import logging
import asyncio
from evdev import UInput, ecodes

logger = logging.getLogger(__name__)

# Initialize the virtual keyboard with specific key capabilities
try:
    capabilities = {
        ecodes.EV_KEY: [ecodes.KEY_LEFTCTRL, ecodes.KEY_V]
    }
    ui = UInput(capabilities, name="bangla-dictation-virtual-kbd")
    import time
    time.sleep(0.5) # Give Wayland time to register the new virtual device
except Exception as e:
    logger.error(f"Failed to create virtual keyboard: {e}")
    ui = None

async def type_text_async(text: str):
    await asyncio.to_thread(type_text, text)

def type_text(text: str):
    """
    Types text into the focused window natively using Wayland clipboard and evdev.
    """
    logger.info(f"Typing text: {text}")
    
    try:
        is_ascii = all(ord(c) < 128 for c in text)
        
        if is_ascii:
            logger.info(f"Executing ydotool type for English text: {text}")
            process = subprocess.run(
                ['ydotool', 'type', '--file', '-'], 
                input=text.encode('utf-8'),
                check=True,
                capture_output=True
            )
            logger.info("ydotool simulated typing successfully.")
            return

        logger.info("Text contains Unicode (Bangla). Falling back to Wayland Clipboard injection...")
        
        if ui is None:
            logger.error("Virtual keyboard not initialized. Cannot paste.")
            return
            
        import time
        # Save clipboard
        original_clipboard = subprocess.run(['wl-paste'], capture_output=True).stdout
        
        # Set new clipboard
        subprocess.run(['wl-copy'], input=text.encode('utf-8'), check=True)
        time.sleep(0.1)
        
        # Press Ctrl
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
        ui.syn()
        time.sleep(0.02)
        
        # Press V
        ui.write(ecodes.EV_KEY, ecodes.KEY_V, 1)
        ui.syn()
        time.sleep(0.02)
        
        # Release V
        ui.write(ecodes.EV_KEY, ecodes.KEY_V, 0)
        ui.syn()
        time.sleep(0.02)
        
        # Release Ctrl
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
        ui.syn()
        time.sleep(0.02)
        
        # Restore clipboard safely
        time.sleep(0.2)
        try:
            subprocess.run(['wl-copy'], input=original_clipboard, check=False)
        except Exception as e:
            logger.error(f"Failed to restore clipboard: {e}")
            
        logger.info("Ctrl+V simulated successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"ydotool failed with code {e.returncode}: {e.stderr.decode('utf-8')}")
    except Exception as general_ex:
        logger.error(f"Typing error: {general_ex}")
