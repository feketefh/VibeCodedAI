# jarvis_ui.py
import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import json
from pathlib import Path

# Text-to-Speech
TTS_AVAILABLE = False
TTS_ENGINE = None
try:
    import pyttsx3
    TTS_AVAILABLE = True
    # Don't initialize here - will be initialized in main thread
except Exception as e:
    print(f"TTS nem elérhető: {e}")

# Voice Recognition - Import from module
try:
    from jarvis_voice_recognition import (
        record_audio,
        transcribe_audio,
        VOICE_AVAILABLE as VOICE_RECOGNITION_AVAILABLE
    )
    print("✓ Voice recognition module loaded")
except Exception as e:
    VOICE_RECOGNITION_AVAILABLE = False
    print(f"⚠ Voice recognition not available: {e}")
    print("Install with: pip install openai-whisper pyaudio")

# ------------------ Beszéd funkció ------------------
def init_tts():
    """Initialize TTS engine in main thread"""
    global TTS_ENGINE
    if TTS_AVAILABLE and TTS_ENGINE is None:
        try:
            import pyttsx3
            TTS_ENGINE = pyttsx3.init()
            TTS_ENGINE.setProperty('rate', 150)
            TTS_ENGINE.setProperty('volume', 0.9)
            print("✓ TTS engine initialized")
        except Exception as e:
            print(f"TTS init error: {e}")
            return False
    return TTS_ENGINE is not None

def speak(text):
    """
    Kimondja a szöveget (ha TTS elérhető).
    Must be called from main thread!
    """
    print(f"[JARVIS]: {text}")
    if TTS_AVAILABLE and TTS_ENGINE:
        try:
            TTS_ENGINE.say(text)
            TTS_ENGINE.runAndWait()
        except Exception as e:
            print(f"TTS hiba: {e}")

# ------------------ Settings Management ------------------
SETTINGS_DIR = Path("jarvis_full_data")
SETTINGS_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = SETTINGS_DIR / "ui_settings.json"

def load_settings():
    """Load UI settings from JSON file"""
    default_config = {
        "tts_enabled": TTS_AVAILABLE,
        "stream_enabled": False
    }

    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(default_config, f, indent=4)
    except Exception as e:
        print(f"Settings load error: {e}")
    
    # Default settings
    return default_config

def save_settings(settings):
    """Save UI settings to JSON file"""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Settings save error: {e}")


# ------------------ Jarvis GUI ------------------
class JarvisGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS AI Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg="#1a1a1a")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize TTS in main thread
        init_tts()
        
        # Load settings from file - use plain dict, not Tkinter vars yet
        self.settings = load_settings()
        
        # Recording state
        self.is_recording = False
        
        # Streaming state
        self.current_stream_message = ""
        self.stream_sender = None  # Track who is sending the stream
        self.stream_queue = queue.Queue()
        
        # TTS queue for thread-safe TTS
        self.tts_queue = queue.Queue()
        
        # Plain Python settings (not Tkinter variables)
        self._tts_enabled = self.settings.get("tts_enabled", TTS_AVAILABLE)
        self._stream_enabled = self.settings.get("stream_enabled", False)
        
        # Title
        self.title_label = tk.Label(
            self.root,
            text="J.A.R.V.I.S. Interface",
            font=("Arial", 24, "bold"),
            fg="#00ff00",
            bg="#1a1a1a"
        )
        self.title_label.pack(pady=20)
        
        # Status indicator
        self.status_label = tk.Label(
            self.root,
            text="● Online",
            font=("Arial", 10),
            fg="#00ff00",
            bg="#1a1a1a"
        )
        self.status_label.pack()
        
        # Chat window
        self.chat_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.chat_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            height=20,
            width=90,
            bg="#0a0a0a",
            fg="#00ff00",
            font=("Courier New", 10),
            insertbackground="#00ff00",
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for streaming
        self.chat_display.tag_config("streaming", foreground="#88ff88")
        
        # Input frame
        self.input_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.input_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Voice record button
        if VOICE_RECOGNITION_AVAILABLE:
            self.record_button = tk.Button(
                self.input_frame,
                text="🎤",
                font=("Arial", 14, "bold"),
                bg="#aa0000",
                fg="white",
                command=self.toggle_recording,
                width=3,
                height=1
            )
            self.record_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Input entry
        self.input_entry = tk.Entry(
            self.input_frame,
            font=("Arial", 12),
            bg="#2a2a2a",
            fg="#00ff00",
            insertbackground="#00ff00"
        )
        self.input_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        self.input_entry.bind("<Return>", lambda e: self.send_message())
        
        # Send button
        self.send_button = tk.Button(
            self.input_frame,
            text="Küldés",
            font=("Arial", 12, "bold"),
            bg="#00aa00",
            fg="white",
            command=self.send_message,
            width=10
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Settings frame
        self.settings_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.settings_frame.pack(pady=5, padx=20, fill=tk.X)
        
        # TTS toggle - Create Tkinter variable AFTER root is created
        self.tts_enabled = tk.BooleanVar(value=self._tts_enabled)
        self.tts_checkbox = tk.Checkbutton(
            self.settings_frame,
            text="🔊 Enable TTS",
            variable=self.tts_enabled,
            bg="#1a1a1a",
            fg="#00ff00",
            selectcolor="#1a1a1a",
            activebackground="#1a1a1a",
            activeforeground="#00ff00",
            font=("Arial", 10),
            command=self.on_tts_toggle
        )
        self.tts_checkbox.pack(side=tk.LEFT, padx=10)
        
        # Streaming toggle
        self.stream_enabled = tk.BooleanVar(value=self._stream_enabled)
        self.stream_checkbox = tk.Checkbutton(
            self.settings_frame,
            text="⚡ Enable Streaming",
            variable=self.stream_enabled,
            bg="#1a1a1a",
            fg="#00ff00",
            selectcolor="#1a1a1a",
            activebackground="#1a1a1a",
            activeforeground="#00ff00",
            font=("Arial", 10),
            command=self.on_stream_toggle
        )
        self.stream_checkbox.pack(side=tk.LEFT, padx=10)
        
        # Clear history button
        self.clear_button = tk.Button(
            self.settings_frame,
            text="🗑️ Clear Chat",
            font=("Arial", 10),
            bg="#aa0000",
            fg="white",
            command=self.clear_chat,
            width=12
        )
        self.clear_button.pack(side=tk.RIGHT, padx=10)
        
        # Start stream processor
        self.process_stream_queue()
        
        # Start TTS processor
        self.process_tts_queue()
        
        # Welcome message
        self.add_message("JARVIS", "Üdvözlöm! Miben segíthetek?")
        
    def add_message(self, sender, message, streaming=False):
        """
        Add message to chat window
        
        Args:
            sender: Message sender name
            message: Message content
            streaming: If True, message is part of a stream
        """
        self.chat_display.config(state=tk.NORMAL)
        
        if streaming:
            # For streaming, append to current message
            self.chat_display.insert(tk.END, message, "streaming")
        else:
            # For regular messages, add with sender
            self.chat_display.insert(tk.END, f"[{sender}]: {message}\n\n")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def start_stream_message(self, sender):
        """Start a new streaming message"""
        self.current_stream_message = ""
        self.stream_sender = sender  # Remember the sender
        # Don't add [JARVIS]: yet - will be added when first content arrives
    
    def end_stream_message(self):
        """End the current streaming message"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.current_stream_message = ""
        self.stream_sender = None
    
    def process_stream_queue(self):
        """Process streaming messages from queue"""
        try:
            while True:
                message = self.stream_queue.get_nowait()
                
                if message == "__START__":
                    self.start_stream_message("JARVIS")
                elif message == "__END__":
                    self.end_stream_message()
                else:
                    # Add [JARVIS]: prefix before first content
                    if self.current_stream_message == "" and hasattr(self, 'stream_sender'):
                        self.chat_display.config(state=tk.NORMAL)
                        self.chat_display.insert(tk.END, f"[{self.stream_sender}]: ", "streaming")
                        self.chat_display.config(state=tk.DISABLED)
                    
                    self.current_stream_message += message
                    self.add_message("", message, streaming=True)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(50, self.process_stream_queue)
    
    def process_tts_queue(self):
        """Process TTS requests from queue (thread-safe)"""
        try:
            while True:
                text = self.tts_queue.get_nowait()
                speak(text)  # Now called from main thread!
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_tts_queue)
    
    def stream_callback(self, text):
        """Callback for streaming text updates"""
        self.stream_queue.put(text)
    
    def on_tts_toggle(self):
        """Called when TTS checkbox is toggled"""
        try:
            self._tts_enabled = self.tts_enabled.get()
            self.settings["tts_enabled"] = self._tts_enabled
            save_settings(self.settings)
            print(f"✓ TTS setting saved: {self._tts_enabled}")
        except Exception as e:
            print(f"TTS toggle error: {e}")
    
    def on_stream_toggle(self):
        """Called when streaming checkbox is toggled"""
        try:
            self._stream_enabled = self.stream_enabled.get()
            self.settings["stream_enabled"] = self._stream_enabled
            save_settings(self.settings)
            print(f"✓ Streaming setting saved: {self._stream_enabled}")
        except Exception as e:
            print(f"Stream toggle error: {e}")
    
    def clear_chat(self):
        """Clear chat history"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Clear conversation history
        from jarvis_logic import clear_history
        clear_history()
        
        self.add_message("JARVIS", "Chat history cleared. Starting fresh!")
    
    def toggle_recording(self):
        """Toggle voice recording on/off"""
        if not VOICE_RECOGNITION_AVAILABLE:
            self.add_message("SYSTEM", "Voice recognition not available. Install: pip install openai-whisper pyaudio")
            return
        
        if not self.is_recording:
            # Start recording
            self.is_recording = True
            self.record_button.config(bg="#ff0000", text="⏹")
            self.status_label.config(text="🎤 Recording... (Click to stop)", fg="#ff0000")
            
            # Start recording in background
            threading.Thread(target=self.start_recording, daemon=True).start()
        else:
            # Stop recording
            self.is_recording = False
            self.record_button.config(bg="#ffaa00", text="⏳")
            self.status_label.config(text="🔄 Processing...", fg="#ffaa00")
    
    def start_recording(self):
        """Start continuous recording until stopped"""
        if not VOICE_RECOGNITION_AVAILABLE:
            return
        
        try:
            import pyaudio
            import wave
            
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            
            audio = pyaudio.PyAudio()
            
            # Open stream
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            print("🎤 Recording started...")
            frames = []
            
            # Record while is_recording is True
            while self.is_recording:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    frames.append(data)
                except Exception as e:
                    print(f"Read error: {e}")
                    break
            
            print("✓ Recording stopped")
            
            # Clean up
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Save to file
            from jarvis_voice_recognition import TEMP_AUDIO_FILE
            with wave.open(str(TEMP_AUDIO_FILE), "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            
            print(f"✓ Audio saved: {TEMP_AUDIO_FILE}")
            
            # Now transcribe the recording
            self.transcribe_recording()
            
        except Exception as e:
            print(f"❌ Recording error: {e}")
            self.root.after(0, lambda: self.status_label.config(text="❌ Recording failed", fg="#ff0000"))
            self.root.after(0, lambda: self.record_button.config(bg="#aa0000", text="🎤"))
            self.is_recording = False
    
    def transcribe_recording(self):
        """Transcribe the recorded audio"""
        try:
            from jarvis_voice_recognition import transcribe_audio, TEMP_AUDIO_FILE
            
            print("🔄 Transcribing audio...")
            
            # Transcribe
            text = transcribe_audio(
                audio_path=TEMP_AUDIO_FILE,
                language="en",
                model_name="large-v3-turbo"
            )
            
            if text:
                # Insert transcribed text into input field ONLY
                self.root.after(0, lambda: self.input_entry.delete(0, tk.END))
                self.root.after(0, lambda: self.input_entry.insert(0, text))
                self.root.after(0, lambda: self.input_entry.focus_set())
                print(f"✓ Transcribed: {text}")
                
            else:
                self.root.after(0, lambda: self.status_label.config(text="❌ Transcription failed", fg="#ff0000"))
        
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            self.root.after(0, lambda: self.status_label.config(text="❌ Transcription failed", fg="#ff0000"))
        
        finally:
            # Reset recording state
            self.is_recording = False
            self.root.after(0, lambda: self.record_button.config(bg="#aa0000", text="🎤"))
            self.root.after(0, lambda: self.status_label.config(text="● Online", fg="#00ff00"))
    
    def send_message(self):
        """Send user message"""
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
        
        self.add_message("YOU", user_input)
        self.input_entry.delete(0, tk.END)
        
        # Use plain Python values (not Tkinter variables)
        tts_enabled = self._tts_enabled
        stream_enabled = self._stream_enabled
        
        # Disable input while processing
        self.input_entry.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.status_label.config(text="🤔 Thinking...", fg="#ffaa00")
        
        # Process input in background with settings as parameters
        threading.Thread(
            target=self.process_input,
            args=(user_input, tts_enabled, stream_enabled),
            daemon=True
        ).start()
    
    def process_input(self, user_input, tts_enabled, stream_enabled):
        """
        Process user input and get AI response
        
        Args:
            user_input: User's message
            tts_enabled: TTS setting (passed as value, not variable)
            stream_enabled: Streaming setting (passed as value, not variable)
        """
        from jarvis_logic import askAI
        import time
        
        try:
            full_response = ""
            
            # Use streaming if enabled
            if stream_enabled:
                ## Signal start of stream
                #self.stream_queue.put("__START__")
                #
                ## Capture streaming response with delay
                #def capture_stream(text):
                #    nonlocal full_response
                #    full_response += text
                #    self.stream_callback(text)
                #    # Add small delay for smooth streaming effect
                #    time.sleep(0.05)  # 50ms delay between words
                
                # Get response with streaming
                response = askAI(user_input)
                
                # Signal end of stream
                #self.stream_queue.put("__END__")
            else:
                # Get response without streaming
                response = askAI(user_input)
                full_response = response
                self.root.after(0, lambda r=response: self.add_message("JARVIS", r))
            
            # TTS (queue it to be spoken in main thread)
            if tts_enabled and full_response:
                self.tts_queue.put(full_response)
        
        except Exception as e:
            import traceback
            error_msg = f"Error: {e}"
            traceback.print_exc()  # Print full error for debugging
            self.root.after(0, lambda: self.add_message("SYSTEM", error_msg))
        
        finally:
            # Re-enable input
            self.root.after(0, lambda: self.input_entry.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_label.config(text="● Online", fg="#00ff00"))
            self.root.after(0, lambda: self.input_entry.focus_set())
    
    def run(self):
        """Start GUI main loop"""
        self.root.mainloop()

    def on_close(self):
        try:
            self.root.destroy()
        except:
            pass
