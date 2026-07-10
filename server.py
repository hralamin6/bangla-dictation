import asyncio
import websockets
import json
import logging
import typer
import socket
import threading

logger = logging.getLogger(__name__)

CLIENTS = set()

async def handler(websocket, path=None):
    CLIENTS.add(websocket)
    logger.info("Browser connected to WebSocket")
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "transcript":
                text = data.get("text", "")
                if text:
                    logger.info(f"Received transcript: {text}")
                    asyncio.create_task(typer.type_text_async(text))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CLIENTS.remove(websocket)
        logger.info("Browser disconnected")

async def send_command(command: str):
    if CLIENTS:
        message = json.dumps({"command": command})
        await asyncio.gather(*[client.send(message) for client in CLIENTS])
    else:
        logger.warning("No browser connected to receive command")

async def _run_server(port):
    async with websockets.serve(handler, "localhost", port):
        await asyncio.Future()  # run forever

def start_udp_listener(loop):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 8766))
    is_recording = False
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            msg = data.decode('utf-8').strip()
            if msg == "toggle":
                is_recording = not is_recording
                cmd = "start" if is_recording else "stop"
                logger.info(f"Toggle triggered via IPC. Command: {cmd}")
                asyncio.run_coroutine_threadsafe(send_command(cmd), loop)
            elif msg in ("start", "stop"):
                if msg == "start" and not is_recording:
                    is_recording = True
                    logger.info("Evdev: Start dictation")
                    asyncio.run_coroutine_threadsafe(send_command("start"), loop)
                elif msg == "stop" and is_recording:
                    is_recording = False
                    logger.info("Evdev: Stop dictation")
                    asyncio.run_coroutine_threadsafe(send_command("stop"), loop)
        except Exception as e:
            logger.error(f"UDP listener error: {e}")

def start_server(loop, config):
    asyncio.set_event_loop(loop)
    port = config.get("websocket_port", 8765)
    
    # Start the local UDP IPC listener for Wayland shortcut support
    threading.Thread(target=start_udp_listener, args=(loop,), daemon=True).start()
    
    logger.info(f"WebSocket server listening on ws://localhost:{port}")
    loop.run_until_complete(_run_server(port))
