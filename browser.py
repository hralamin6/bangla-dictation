import os
import subprocess
import logging
import threading
import http.server
import socketserver
import shutil

logger = logging.getLogger(__name__)

def launch_browser(config):
    web_dir = os.path.join(os.path.dirname(__file__), 'web')
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=web_dir, **kwargs)
            
    httpd = socketserver.TCPServer(("", 0), Handler)
    http_port = httpd.server_address[1]
    
    def serve():
        httpd.serve_forever()
        
    threading.Thread(target=serve, daemon=True).start()
    
    url = f"http://localhost:{http_port}"
    logger.info(f"Local web server running at {url}")
    
    chrome_cmds = ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']
    
    browser_cmd = None
    for cmd in chrome_cmds:
        if shutil.which(cmd):
            browser_cmd = cmd
            break
            
    if browser_cmd:
        logger.info(f"Launching {browser_cmd} with URL {url}")
        subprocess.Popen([
            browser_cmd,
            f"--app={url}",
            "--headless=new",
            "--use-fake-ui-for-media-stream"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        logger.error("No compatible browser found. Please install Chrome or Chromium.")
