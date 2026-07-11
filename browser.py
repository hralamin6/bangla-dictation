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
            import re
            
            # Auto-detect language by checking for Bengali characters
            is_bangla = bool(re.search(r'[\u0980-\u09FF]', text))
            
            # Map standard OpenAI voices to Microsoft Edge Neural voices
            if is_bangla:
                voice_map = {
                    'alloy': 'bn-BD-PradeepNeural',     # Male BD (Default)
                    'nova': 'bn-BD-NabanitaNeural',     # Female BD
                    'echo': 'bn-IN-BashkarNeural',      # Male IN
                    'shimmer': 'bn-IN-TanishaaNeural',  # Female IN
                    'fable': 'en-US-GuyNeural',
                    'onyx': 'en-US-AriaNeural'
                }
            else:
                voice_map = {
                    'alloy': 'en-US-AriaNeural',        # Female EN (Default)
                    'nova': 'en-US-JennyNeural',        # Female EN
                    'echo': 'en-US-GuyNeural',          # Male EN
                    'shimmer': 'en-US-ChristopherNeural',# Male EN
                    'fable': 'en-US-GuyNeural',
                    'onyx': 'en-US-AriaNeural'
                }
                
            edge_voice = voice_map.get(voice, 'bn-BD-PradeepNeural' if is_bangla else 'en-US-AriaNeural')
            
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

        def check_authorization(self):
            api_key = config.get('api_key')
            if not api_key:
                return True # No API key configured, allow all
                
            auth_header = self.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": {"message": "Missing Authentication", "type": "invalid_request_error", "param": null, "code": "invalid_api_key"}}')
                return False
                
            provided_key = auth_header.split(' ')[1]
            if provided_key != api_key:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": {"message": "Incorrect API key provided", "type": "invalid_request_error", "param": null, "code": "invalid_api_key"}}')
                return False
                
            return True

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
            elif self.path == '/v1/models':
                if not self.check_authorization():
                    return
                
                import json
                
                # Only list models that work reliably without auth in g4f 7.8.2, plus our custom TTS/STT engines
                models = [
                    "gpt-4o", "gpt-4",        # Chat Completions
                    "flux", "dall-e-3",       # Image Generation
                    "tts-1", "tts-1-hd",      # Text-To-Speech (Edge TTS)
                    "whisper-1"               # Speech-To-Text (Google/Cloud)
                ]
                
                providers = [
                    "Cloudflare", "Copilot", "DeepInfra", "EasyChat", 
                    "Felo", "PollinationsAI", "Yqcloud"
                ]
                
                data = [{"id": m, "object": "model", "owned_by": "g4f-model"} for m in models]
                data.append({"id": "---AVAILABLE-PROVIDERS---", "object": "model", "owned_by": "info"})
                data.extend([{"id": p, "object": "provider", "owned_by": "g4f-provider"} for p in providers])
                
                response = {
                    "object": "list",
                    "data": data
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                super().do_GET()
                
        def do_POST(self):
            if not self.path.startswith('/v1/'):
                self.send_response(404)
                self.end_headers()
                return
                
            if not self.check_authorization():
                return
                
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
            elif self.path == '/v1/chat/completions':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                try:
                    import json
                    import time
                    from g4f.client import Client
                    
                    data = json.loads(post_data.decode('utf-8'))
                    model = data.get('model', 'gpt-4o')
                    provider_name = data.get('provider', None)
                    messages = data.get('messages', [])
                    
                    # Handle Multimodality (Vision)
                    image_bytes = None
                    for message in messages:
                        if isinstance(message.get('content'), list):
                            text_content = ""
                            for item in message['content']:
                                if item.get('type') == 'text':
                                    text_content += item.get('text', '') + "\n"
                                elif item.get('type') == 'image_url':
                                    url = item.get('image_url', {}).get('url', '')
                                    if url.startswith('data:image'):
                                        import base64
                                        b64_data = url.split(',')[1]
                                        image_bytes = base64.b64decode(b64_data)
                                    elif url.startswith('http'):
                                        import urllib.request
                                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                                        with urllib.request.urlopen(req) as res:
                                            image_bytes = res.read()
                            message['content'] = text_content.strip()
                    
                    client = Client()
                    kwargs = {"model": model, "messages": messages}
                    if image_bytes:
                        kwargs["image"] = image_bytes
                        
                    if provider_name:
                        import g4f
                        from g4f.Provider import ProviderUtils
                        
                        provider_class = None
                        # Case-insensitive provider search using g4f's internal map
                        for name in ProviderUtils.convert.keys():
                            if name.lower() == provider_name.lower():
                                provider_class = ProviderUtils.convert[name]
                                break
                                
                        if provider_class:
                            kwargs["provider"] = provider_class
                        else:
                            raise ValueError(f"Provider not found: {provider_name}")
                        
                    stream = data.get('stream', False)
                    kwargs["stream"] = stream
                        
                    response = client.chat.completions.create(**kwargs)
                    
                    if stream:
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
                        self.send_header('Cache-Control', 'no-cache')
                        self.send_header('Connection', 'keep-alive')
                        self.end_headers()
                        
                        for chunk in response:
                            content_obj = chunk.choices[0].delta.content if hasattr(chunk, 'choices') and chunk.choices else None
                            if content_obj is not None:
                                content_str = str(content_obj)
                                chunk_data = {
                                    "id": f"chatcmpl-{int(time.time())}",
                                    "object": "chat.completion.chunk",
                                    "created": int(time.time()),
                                    "model": model,
                                    "choices": [
                                        {
                                            "index": 0,
                                            "delta": {"content": content_str},
                                            "finish_reason": None
                                        }
                                    ]
                                }
                                self.wfile.write(f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n".encode('utf-8'))
                                self.wfile.flush()
                                
                        self.wfile.write(b"data: [DONE]\n\n")
                        self.wfile.flush()
                        return
                    
                    content_obj = response.choices[0].message.content if hasattr(response, 'choices') and response.choices else str(response)
                    content_str = str(content_obj) if content_obj is not None else ""
                    
                    openai_format = {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": content_str,
                            },
                            "finish_reason": "stop"
                        }],
                        "usage": {
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0
                        }
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(openai_format, ensure_ascii=False).encode('utf-8'))
                    
                except Exception as e:
                    logger.error(f"OpenAI API Chat error: {e}")
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Internal Server Error"}')
            elif self.path == '/v1/images/generations':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                try:
                    import json
                    import time
                    from g4f.client import Client
                    
                    data = json.loads(post_data.decode('utf-8'))
                    prompt = data.get('prompt', '')
                    model = data.get('model', 'flux')
                    response_format = data.get('response_format', 'b64_json')
                    
                    if not prompt:
                        raise ValueError("Prompt is required")
                        
                    client = Client()
                    response = client.images.generate(
                        model=model,
                        prompt=prompt,
                        response_format=response_format
                    )
                    
                    if response_format == 'b64_json':
                        image_data = {"b64_json": response.data[0].b64_json}
                    else:
                        image_data = {"url": response.data[0].url}
                    
                    openai_format = {
                        "created": int(time.time()),
                        "data": [
                            image_data
                        ]
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(openai_format, ensure_ascii=False).encode('utf-8'))
                    
                except Exception as e:
                    logger.error(f"OpenAI API Image Gen error: {e}")
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
