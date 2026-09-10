import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from providers.tts_bhashini import BhashiniTTSProvider

def test_tts():
    try:
        provider = BhashiniTTSProvider()
    except Exception as e:
        print(f"Failed to init provider: {e}")
        return

    tests = [
        {"lang": "hi", "text": "आज आपकी सबसे बड़ी परेशानी क्या है?", "file": "../tmp/test_hi.mp3"},
        {"lang": "en", "text": "What is your main problem today?", "file": "../tmp/test_en.mp3"}
    ]

    for t in tests:
        print(f"\n--- Testing TTS {t['lang']} ---")
        start = time.time()
        try:
            audio_bytes = provider.synthesize(t["text"], t["lang"])
            latency = int((time.time() - start) * 1000)
            print(f"config status: OK")
            print(f"inference status: OK")
            print(f"provider=BhashiniTTSProvider")
            print(f"audio byte size: {len(audio_bytes)}")
            print(f"latency: {latency}ms")
            
            with open(os.path.join(os.path.dirname(__file__), t["file"]), "wb") as f:
                f.write(audio_bytes)
            print(f"Wrote to {t['file']}")
            
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    test_tts()
