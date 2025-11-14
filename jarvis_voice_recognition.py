# jarvis_voice_recognition.py
# Complete voice recognition module with recording and transcription
import wave
from pathlib import Path

# Voice Recognition
VOICE_AVAILABLE = False
try:
    import whisper
    import pyaudio
    import numpy as np
    VOICE_AVAILABLE = True
    print("✓ Voice recognition loaded")
except Exception as e:
    print(f"⚠ Voice recognition not available: {e}")
    print("Install with: pip install openai-whisper pyaudio")

# ------------------ Configuration ------------------
DATA_DIR = Path("jarvis_full_data")
DATA_DIR.mkdir(exist_ok=True)
TEMP_AUDIO_FILE = DATA_DIR / "temp_recording.wav"

# Whisper model (loaded on first use)
whisper_model = None
CURRENT_MODEL = "base"  # Options: tiny, base, small, medium, large, large-v3-turbo

# ------------------ Model Management ------------------
def load_whisper_model(model_name="base"):
    """
    Load Whisper model (lazy loading)
    
    Args:
        model_name: Model size (tiny, base, small, medium, large, large-v3-turbo)
    
    Returns:
        Loaded model or None if failed
    """
    global whisper_model, CURRENT_MODEL
    
    if not VOICE_AVAILABLE:
        print("❌ Whisper not available")
        return None
    
    if whisper_model is not None and CURRENT_MODEL == model_name:
        return whisper_model
    
    try:
        print(f"🔄 Loading Whisper model: {model_name}")
        whisper_model = whisper.load_model(model_name)
        CURRENT_MODEL = model_name
        print(f"✓ Whisper model '{model_name}' loaded")
        return whisper_model
    except Exception as e:
        print(f"❌ Failed to load Whisper model: {e}")
        return None

# ------------------ Audio Recording ------------------
def record_audio(duration=5, sample_rate=16000):
    """
    Record audio from microphone
    
    Args:
        duration: Recording duration in seconds (default: 5)
        sample_rate: Audio sample rate (default: 16000)
    
    Returns:
        Path to saved audio file or None if failed
    """
    if not VOICE_AVAILABLE:
        print("❌ PyAudio not available")
        return None
    
    try:
        audio = pyaudio.PyAudio()
        
        # Find default input device
        try:
            default_device = audio.get_default_input_device_info()
            print(f"🎤 Using microphone: {default_device['name']}")
        except:
            print("⚠ No default microphone found, trying anyway...")
        
        # Open audio stream
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=1024
        )
        
        print(f"🎤 Recording for {duration} seconds...")
        frames = []
        
        # Record audio in chunks
        for i in range(0, int(sample_rate / 1024 * duration)):
            try:
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)
            except Exception as e:
                print(f"⚠ Read error: {e}")
                break
        
        print("✓ Recording complete")
        
        # Clean up
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Save to WAV file
        with wave.open(str(TEMP_AUDIO_FILE), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
        
        print(f"✓ Audio saved: {TEMP_AUDIO_FILE}")
        return TEMP_AUDIO_FILE
        
    except Exception as e:
        print(f"❌ Recording error: {e}")
        return None

# ------------------ Audio Transcription ------------------
def transcribe_audio(audio_path, language="hu", model_name="base"):
    """
    Transcribe audio file using Whisper
    
    Args:
        audio_path: Path to audio file
        language: Language code (default: "hu" for Hungarian, None for auto-detect)
        model_name: Whisper model to use
    
    Returns:
        Transcribed text or None if failed
    """
    if not VOICE_AVAILABLE:
        print("❌ Whisper not available")
        return None
    
    if not audio_path or not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return None
    
    try:
        # Load model if needed
        model = load_whisper_model(model_name)
        if model is None:
            return None
        
        print(f"🔄 Transcribing audio (language: {language if language else 'auto'})...")
        
        # Transcribe with options
        result = model.transcribe(
            str(audio_path),
            language=language,
            fp16=False  # Use FP32 for CPU compatibility
        )
        
        text = result["text"].strip()
        detected_lang = result.get("language", "unknown")
        
        print(f"✓ Transcription complete (detected: {detected_lang})")
        print(f"📝 Text: {text}")
        
        return text
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return None

# ------------------ List Available Devices ------------------
def list_audio_devices():
    """List all available audio input devices"""
    if not VOICE_AVAILABLE:
        print("❌ PyAudio not available")
        return
    
    try:
        audio = pyaudio.PyAudio()
        
        print("\n" + "="*60)
        print("🎤 Available Audio Devices")
        print("="*60)
        
        info = audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(0, num_devices):
            device_info = audio.get_device_info_by_host_api_device_index(0, i)
            
            if device_info.get('maxInputChannels') > 0:
                print(f"\n[Device {i}]")
                print(f"  Name: {device_info.get('name')}")
                print(f"  Channels: {device_info.get('maxInputChannels')}")
                print(f"  Sample Rate: {device_info.get('defaultSampleRate')}")
        
        print("\n" + "="*60 + "\n")
        
        audio.terminate()
        
    except Exception as e:
        print(f"❌ Error listing devices: {e}")


# ------------------ Get Available Models ------------------
def get_available_models():
    """Return list of available Whisper models"""
    return {
        "tiny": {"size": "~75MB", "speed": "⚡⚡⚡", "quality": "⭐⭐"},
        "base": {"size": "~150MB", "speed": "⚡⚡⚡", "quality": "⭐⭐⭐"},
        "small": {"size": "~500MB", "speed": "⚡⚡", "quality": "⭐⭐⭐⭐"},
        "medium": {"size": "~1.5GB", "speed": "⚡", "quality": "⭐⭐⭐⭐"},
        "large": {"size": "~3GB", "speed": "⚡", "quality": "⭐⭐⭐⭐⭐"},
        "large-v3-turbo": {"size": "~1.5GB", "speed": "⚡⚡", "quality": "⭐⭐⭐⭐⭐"}
    }

def print_model_info():
    """Print information about available models"""
    models = get_available_models()
    
    print("\n" + "="*60)
    print("📊 Available Whisper Models")
    print("="*60)
    
    for model_name, info in models.items():
        print(f"\n{model_name}:")
        print(f"  Size: {info['size']}")
        print(f"  Speed: {info['speed']}")
        print(f"  Quality: {info['quality']}")
    
    print("\n" + "="*60)
    print("Recommendation: 'base' for good balance, 'small' for better quality")
    print("="*60 + "\n")

