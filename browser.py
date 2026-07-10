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
            
        def generate_edge_tts(self, text, voice, speed=1.0):
            import subprocess
            import os
            
            # Map standard OpenAI voices to Microsoft Edge Neural Bangla voices
            voice_map = {
                'alloy': 'bn-BD-PradeepNeural',     # Male BD (Default)
                'nova': 'bn-BD-NabanitaNeural',     # Female BD
                'echo': 'bn-IN-BashkarNeural',      # Male IN
                'shimmer': 'bn-IN-TanishaaNeural',  # Female IN
                'fable': 'en-US-GuyNeural',         # English Male
                'onyx': 'en-US-AriaNeural'          # English Female
            }
            edge_voice = voice_map.get(voice, 'bn-BD-PradeepNeural')
            
            # Convert OpenAI speed multiplier (0.25 to 4.0) to Edge TTS percentage
            rate_pct = int((speed - 1.0) * 100)
            rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"
            
            # Get path to edge-tts binary
            edge_tts_bin = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'edge-tts')
            
            # Run edge-tts to generate audio bytes
            process = subprocess.run([
                edge_tts_bin,
                '--voice', edge_voice,
                '--rate', rate_str,
                '--text', text
            ], capture_output=True)
            
            if process.returncode != 0:
                raise Exception(f"Edge TTS failed: {process.stderr.decode('utf-8')}")
                
            return process.stdout

        def do_GET(self):
            if self.path.startswith('/tts?'):
                from urllib.parse import urlparse, parse_qs
                
                query = parse_qs(urlparse(self.path).query)
                text = query.get('text', [''])[0]
                # Default Web UI uses alloy (Pradeep)
                voice = query.get('voice', ['alloy'])[0] 
                
                try:
                    audio_data = self.generate_edge_tts(text, voice)
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/mpeg')
                    self.end_headers()
                    self.wfile.write(audio_data)
                except Exception as e:
                    logger.error(f"TTS Proxy error: {e}")
                    self.send_response(500)
                    self.end_headers()
            else:
                super().do_GET()
                
        def do_POST(self):
            if self.path == '/v1/audio/speech':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                try:
                    import json
                    
                    data = json.loads(post_data.decode('utf-8'))
                    text = data.get('input', '')
                    voice = data.get('voice', 'alloy')
                    speed = float(data.get('speed', 1.0))
                    
                    audio_data = self.generate_edge_tts(text, voice, speed)
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/mpeg')
                    self.end_headers()
                    self.wfile.write(audio_data)
                except Exception as e:
                    logger.error(f"OpenAI API TTS error: {e}")
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Internal Server Error"}')
            elif self.path == '/v1/audio/transcriptions':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                try:
                    import json
                    import tempfile
                    import subprocess
                    import os
                    from email.parser import BytesParser
                    import speech_recognition as sr
                    
                    # Parse multipart/form-data using standard library
                    msg = BytesParser().parsebytes(
                        b"Content-Type: " + self.headers['Content-Type'].encode() + b"\r\n\r\n" + post_data
                    )
                    
                    audio_bytes = None
                    language = 'bn-BD'
                    
                    for part in msg.walk():
                        if part.get_filename():
                            audio_bytes = part.get_payload(decode=True)
                        elif part.get_param('name', header='content-disposition') == 'language':
                            language = part.get_payload(decode=True).decode('utf-8')
                            
                    if not audio_bytes:
                        raise ValueError("No file uploaded")
                        
                    # Save to temp file and convert to WAV using ffmpeg
                    with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
                        f.write(audio_bytes)
                        tmp_path = f.name
                        
                    wav_path = tmp_path + ".wav"
                    try:
                        import imageio_ffmpeg
                        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                        
                        subprocess.run([ffmpeg_exe, '-y', '-i', tmp_path, '-ar', '16000', '-ac', '1', wav_path], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                                     
                        recognizer = sr.Recognizer()
                        with sr.AudioFile(wav_path) as source:
                            audio = recognizer.record(source)
                            
                        # Map standard OpenAI language codes
                        if language == 'bn': language = 'bn-BD'
                        if language == 'en': language = 'en-US'
                        
                        text = recognizer.recognize_google(audio, language=language)
                    finally:
                        if os.path.exists(tmp_path): os.remove(tmp_path)
                        if os.path.exists(wav_path): os.remove(wav_path)
                        
                    response = json.dumps({"text": text}, ensure_ascii=False).encode('utf-8')
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(response)
                    
                except sr.UnknownValueError:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"text": ""}')
                except Exception as e:
                    logger.error(f"OpenAI API STT error: {e}")
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Internal Server Error"}')
            else:
                self.send_response(404)
                self.end_headers()
            
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
        
    try:
        httpd = ReusableTCPServer(("", 8767), Handler)
    except OSError:
        # Fallback to dynamic port if 8767 is in use
        httpd = ReusableTCPServer(("", 0), Handler)
        
    http_port = httpd.server_address[1]
    
    def serve():
        httpd.serve_forever()
        
    threading.Thread(target=serve, daemon=True).start()
    
    url = f"http://localhost:{http_port}"
    logger.info(f"Local web server running at {url}")
    
    mode = config.get("mode", "1")
    if mode == "1":
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
                "--use-fake-ui-for-media-stream",
                "--autoplay-policy=no-user-gesture-required"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            logger.error("No compatible browser found. Please install Chrome or Chromium.")
