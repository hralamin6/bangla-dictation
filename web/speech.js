const statusEl = document.getElementById('status');
const transcriptEl = document.getElementById('transcript');

let ws;
let recognition;
let isRecording = false;
let configLanguage = 'bn-BD';

// Initialize WebSocket
function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8765');
    
    ws.onopen = () => {
        statusEl.textContent = 'Ready (Press Ctrl+Space)';
        statusEl.className = 'ready';
        console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.command === 'start_en') {
            configLanguage = 'en-US';
            if (recognition) recognition.lang = configLanguage;
            startDictation();
        } else if (data.command === 'start_bn') {
            configLanguage = 'bn-BD';
            if (recognition) recognition.lang = configLanguage;
            startDictation();
        } else if (data.command === 'stop') {
            stopDictation();
        } else if (data.command === 'speak') {
            // Stop any playing audio
            if (window.currentAudio) {
                window.currentAudio.pause();
                window.currentAudio = null;
            }
            window.speechSynthesis.cancel(); 
            
            if (data.text) {
                // Use Google Translate's unofficial high-quality TTS endpoint
                const lang = (data.lang || 'bn').split('-')[0]; // Extract 'bn' or 'en'
                
                // Google Translate TTS limits strings to ~200 chars. Split by spaces into chunks.
                const chunks = data.text.match(/.{1,150}(?:\s|$)/g) || [data.text];
                let currentChunkIndex = 0;
                
                function playNextChunk() {
                    if (currentChunkIndex >= chunks.length) return;
                    
                    const chunkText = encodeURIComponent(chunks[currentChunkIndex].trim());
                    if (!chunkText) {
                        currentChunkIndex++;
                        playNextChunk();
                        return;
                    }
                    
                    // Route through local python server proxy to bypass strict browser CORS/CORP
                    const url = `/tts?lang=${lang}&text=${chunkText}`;
                    const audio = new Audio(url);
                    window.currentAudio = audio;
                    
                    audio.onended = () => {
                        currentChunkIndex++;
                        playNextChunk();
                    };
                    
                    audio.play().catch(e => console.error("Audio play failed:", e));
                }
                
                playNextChunk();
            }
        }
    };

    // Pre-load voices
    window.speechSynthesis.getVoices();
    
    ws.onclose = () => {
        statusEl.textContent = 'Disconnected. Reconnecting...';
        statusEl.className = '';
        setTimeout(connectWebSocket, 2000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket Error:', error);
    };
}

// Initialize Speech Recognition
function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        statusEl.textContent = 'Speech Recognition API not supported in this browser.';
        statusEl.style.backgroundColor = 'red';
        return;
    }
    
    recognition = new SpeechRecognition();
    recognition.lang = configLanguage;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = true;
    
    recognition.onresult = (event) => {
        let text = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                text += event.results[i][0].transcript;
            }
        }
        
        if (text.trim() !== '') {
            transcriptEl.textContent = text;
            
            // Send back to Python
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'transcript', text: text.trim() }));
            }
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Speech Recognition Error:', event.error);
        if (event.error === 'not-allowed') {
            statusEl.textContent = 'Microphone permission denied.';
        }
    };
    
    recognition.onend = () => {
        if (isRecording) {
            // Restart if it stopped unexpectedly while hotkey is held
            try {
                recognition.start();
            } catch(e) {}
        } else {
            statusEl.textContent = 'Ready (Press Ctrl+Space)';
            statusEl.className = 'ready';
        }
    };
}

function startDictation() {
    if (!recognition || isRecording) return;
    
    isRecording = true;
    statusEl.textContent = 'Listening...';
    statusEl.className = 'listening';
    transcriptEl.textContent = '';
    
    try {
        recognition.start();
    } catch (e) {
        console.error(e);
    }
}

function stopDictation() {
    if (!recognition || !isRecording) return;
    
    isRecording = false;
    try {
        recognition.stop();
    } catch (e) {
        console.error(e);
    }
}

setupSpeechRecognition();
connectWebSocket();
