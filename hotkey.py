import evdev
from evdev import ecodes
import asyncio
import logging
from server import send_command, send_payload
import subprocess

logger = logging.getLogger(__name__)

async def monitor_device(device, loop):
    is_recording = False
    r_ctrl_pressed = False
    r_alt_pressed = False
    l_ctrl_pressed = False
    tts_triggered = False
    start_task = None
    
    async def trigger_start():
        nonlocal is_recording, start_task, tts_triggered
        await asyncio.sleep(0.15) # Wait 150ms to see if Alt/LeftCtrl is also pressed
        
        if r_ctrl_pressed and l_ctrl_pressed:
            tts_triggered = True
            logger.info("Evdev: Right Ctrl + Left Ctrl. Triggering TTS for clipboard...")
            try:
                # Read from Wayland clipboard
                clipboard_text = subprocess.run(['wl-paste'], capture_output=True, text=True).stdout.strip()
                if clipboard_text:
                    asyncio.run_coroutine_threadsafe(
                        send_payload({"command": "speak", "text": clipboard_text, "lang": "bn-BD"}), loop
                    )
            except Exception as e:
                logger.error(f"Failed to read clipboard for TTS: {e}")
        elif r_ctrl_pressed and r_alt_pressed:
            is_recording = True
            logger.info("Evdev: Right Ctrl + Right Alt. Starting Bangla dictation...")
            asyncio.run_coroutine_threadsafe(send_command("start_bn"), loop)
        elif r_ctrl_pressed:
            is_recording = True
            logger.info("Evdev: Right Ctrl only. Starting English dictation...")
            asyncio.run_coroutine_threadsafe(send_command("start_en"), loop)
            
        start_task = None

    try:
        async for event in device.async_read_loop():
            if event.type == ecodes.EV_KEY:
                if event.code == ecodes.KEY_RIGHTCTRL:
                    r_ctrl_pressed = (event.value == 1 or event.value == 2)
                elif event.code == ecodes.KEY_RIGHTALT:
                    r_alt_pressed = (event.value == 1 or event.value == 2)
                elif event.code == ecodes.KEY_LEFTCTRL:
                    l_ctrl_pressed = (event.value == 1 or event.value == 2)
                    
                if r_ctrl_pressed and not is_recording and not tts_triggered and start_task is None:
                    start_task = asyncio.create_task(trigger_start())
                    
                if is_recording and not r_ctrl_pressed:
                    is_recording = False
                    if start_task:
                        start_task.cancel()
                        start_task = None
                    logger.info("Evdev: Keys released. Stopping dictation...")
                    asyncio.run_coroutine_threadsafe(send_command("stop"), loop)
                    
                if not r_ctrl_pressed and not l_ctrl_pressed:
                    tts_triggered = False
                    
    except (OSError, IOError):
        pass # Device disconnected

def setup_hotkeys(config, loop):
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    keyboards = []
    
    for device in devices:
        caps = device.capabilities()
        if ecodes.EV_KEY in caps and ecodes.KEY_SPACE in caps[ecodes.EV_KEY]:
            keyboards.append(device)
            
    if not keyboards:
        logger.error("No keyboards found! You must be in the 'input' group to read hardware keys.")
        return
        
    logger.info(f"Evdev: Monitoring {len(keyboards)} keyboards for Right Ctrl + Right Alt...")
    for kb in keyboards:
        asyncio.run_coroutine_threadsafe(monitor_device(kb, loop), loop)
