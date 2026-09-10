import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from dotenv import load_dotenv
load_dotenv(os.path.join(sys.path[-1], '.env'))

from gtts import gTTS
from pydub import AudioSegment
from providers.asr_ai4bharat import AI4BharatASRProvider

def test_asr():
    print("1. Generating Hindi audio sample ('Mujhe do din se bukhar hai')...")
    tts = gTTS(text="मुझे दो दिन से बुखार है", lang="hi")
    mp3_path = "sample_hi.mp3"
    tts.save(mp3_path)
    
    print("2. Converting to WAV format...")
    wav_path = "sample_hi.wav"
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")
    
    print("3. Loading AI4Bharat IndicConformer Model (this may take a moment to download weights)...")
    provider = AI4BharatASRProvider()
    
    device_str = "cpu"
    try:
        if hasattr(provider.model, 'device'):
            device_str = str(provider.model.device)
        else:
            device_str = str(next(provider.model.parameters()).device)
    except StopIteration:
        device_str = "cpu (inferred)"
        
    print(f"Model loaded successfully on device: {device_str}")
    
    print("4. Transcribing...")
    transcript = provider.transcribe(wav_path, "hi")
    
    print(f"\n--- TRANSCRIPTION RESULT ---")
    print(f"Output: {transcript}")
    print("----------------------------\n")
    
    os.remove(mp3_path)
    os.remove(wav_path)

if __name__ == "__main__":
    test_asr()
