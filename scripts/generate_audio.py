import os
import sys

# Add backend directory to sys.path to import models and database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal, init_db
from backend.models import Question
from backend.providers.factory import get_tts_provider

# Directories for static audio
AUDIO_DIR_HI = os.path.join(os.path.dirname(__file__), '../frontend/public/audio/hi')
AUDIO_DIR_EN = os.path.join(os.path.dirname(__file__), '../frontend/public/audio/en')

def ensure_dirs():
    os.makedirs(AUDIO_DIR_HI, exist_ok=True)
    os.makedirs(AUDIO_DIR_EN, exist_ok=True)

def generate_audio():
    ensure_dirs()
    init_db()
    db = SessionLocal()
    
    provider = get_tts_provider()
    questions = db.query(Question).all()
    
    print(f"Found {len(questions)} questions. Starting audio generation...")
    
    for q in questions:
        # Generate Hindi
        hi_path = os.path.join(AUDIO_DIR_HI, f"q{q.id}.mp3")
        if not os.path.exists(hi_path) and q.text_hi:
            try:
                audio_bytes = provider.synthesize(q.text_hi, "hi")
                if audio_bytes:
                    with open(hi_path, "wb") as f:
                        f.write(audio_bytes)
                    print(f"Generated HI for Q{q.id}")
            except Exception as e:
                print(f"Failed to generate HI for Q{q.id}: {e}")

        # Generate English
        en_path = os.path.join(AUDIO_DIR_EN, f"q{q.id}.mp3")
        if not os.path.exists(en_path) and q.text_en:
            try:
                audio_bytes = provider.synthesize(q.text_en, "en")
                if audio_bytes:
                    with open(en_path, "wb") as f:
                        f.write(audio_bytes)
                    print(f"Generated EN for Q{q.id}")
            except Exception as e:
                print(f"Failed to generate EN for Q{q.id}: {e}")
                
    db.close()
    print("Audio generation complete.")

if __name__ == "__main__":
    # Note: Requires TTS provider keys to be set in the environment or uses MockTTSProvider
    generate_audio()
