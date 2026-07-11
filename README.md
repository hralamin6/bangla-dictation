# Bangla Dictation & AI API Server (Linux)

A lightweight, headless background service for Ubuntu/Pop!_OS that provides **Global Dictation Hotkeys** and a **Local OpenAI-Compatible API Server** for advanced Speech-to-Text (STT) and Text-to-Speech (TTS).

## Features

1. **Global Dictation**
   - Press and hold `Right Ctrl` ➔ English Dictation
   - Press and hold `Right Ctrl + Right Alt` ➔ Bangla Dictation
   - Injects transcribed text instantly across Wayland/X11 directly into your cursor.

2. **OpenAI-Compatible API (Local Server)**
   - Exposes `http://localhost:8767/v1/audio/transcriptions` for processing pre-recorded MP3/WAV files.
   - Exposes `http://localhost:8767/v1/audio/speech` for generating high-quality Edge TTS audio.
   - Drop-in replacement for any app that uses OpenAI's API.

3. **High-Quality Neural TTS**
   - Supports 4 beautiful Bengali Neural Voices powered by Microsoft Edge.
   - Global Hotkey: Highlight text, copy (`Ctrl+C`), and press `Left Ctrl + Right Ctrl` to read it out loud.

## Installation

Run the installation script to grab dependencies and create the python virtual environment. **It will ask you if you want the Full Experience (Hotkeys + API) or just the API Server (lower memory, no hotkeys).**

```bash
./install.sh
```

**Important for Hotkey Mode**: You *must* add your user to the `input` group so the script can monitor hotkeys:
```bash
sudo usermod -aG input $USER
```
*(You must log out and log back in for this group change to take effect).*

## How to run (Autostart on Boot)

To have the daemon automatically start silently every time you turn on your computer:

```bash
mkdir -p ~/.config/systemd/user/
cp bangla-dictation.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now bangla-dictation.service
```

## Updating / Upgrading

If you want to pull the latest features and bug fixes from GitHub, make sure you update your python dependencies afterwards:

```bash
git pull origin main
./venv/bin/pip install -r requirements.txt
systemctl --user restart bangla-dictation.service
```

## API Documentation (Port 8767)

### Chat Completions (LLM Text Generation)
Generate text using powerful LLMs (GPT-4o) completely for free by hijacking web interfaces using the integrated `g4f` engine. 

**Features:**
- Supports full Server-Sent Events (SSE) streaming by passing `"stream": true`!
- Automatically routes to the best free web provider (just omit the `"provider"` field).

```bash
curl http://localhost:8767/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "stream": true,
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "আমাকে বাংলা ভাষা সম্পর্কে কিছু বলুন।"}
    ]
  }'
```

### Image Generation (Text to Image)
Generate beautiful images completely for free using the ultra-fast Flux AI model.

**Features:**
- Defaults to returning standard `"b64_json"` (base64 string) just like OpenAI.
- If you prefer a direct link, pass `"response_format": "url"`.

```bash
curl http://localhost:8767/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "model": "flux",
    "response_format": "url",
    "prompt": "একটি সুন্দর বাংলাদেশী গ্রামের ছবি, ডিজিটাল আর্ট"
  }'
```

### Speech-To-Text (STT)
Transcribe pre-recorded audio files (`.mp3`, `.wav`, `.m4a`) into text. Powered by Google Cloud Speech (no API key needed).

**Features:**
- The `language` field defaults to `"bn-BD"` (Bengali) if omitted. You can pass `"en"` for English.

```bash
curl http://localhost:8767/v1/audio/transcriptions \
  -F file="@/path/to/test.mp3" \
  -F model="whisper-1" \
  -F language="bn"
```

### Text-To-Speech (TTS)
Generate high-quality audio from text using Microsoft Edge Neural voices.

**Features:**
- The engine **automatically detects** if your text is Bengali or English and routes it to the appropriate regional native speaker!

```bash
curl http://localhost:8767/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "হ্যালো, আমি একটি এপিআই থেকে কথা বলছি!",
    "voice": "alloy",
    "speed": 1.0
  }' --output test.mp3
```

### List Available Models & Providers
See exactly which LLM models and Free Web Providers you can manually select from.

```bash
curl http://localhost:8767/v1/models
```
