import whisper
import pyaudio
import wave

# Load model (downloads automatically)
model = whisper.load_model("large-v3-turbo")  # tiny, base, small, medium, large

def listen_and_transcribe():
    # Record audio
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, 
                       rate=16000, input=True, frames_per_buffer=1024)
    
    print("Listening...")
    frames = []
    for _ in range(0, int(16000 / 1024 * 5)):  # 5 seconds
        data = stream.read(1024)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # Save and transcribe
    with wave.open("temp_audio.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
    
    result = model.transcribe("temp_audio.wav")
    return result["text"]