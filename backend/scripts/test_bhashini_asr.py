import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from providers.asr_bhashini import BhashiniASRProvider

def test_asr():
    try:
        provider = BhashiniASRProvider()
    except Exception as e:
        print(f"Failed to init provider: {e}")
        return

    tests = [
        {"lang": "hi", "file": "../tmp/test_hi.wav"},
        {"lang": "en", "file": "../tmp/test_en.wav"}
    ]

    for t in tests:
        print(f"\n--- Testing ASR {t['lang']} ---")
        start = time.time()
        try:
            # The transcribe method in BhashiniASRProvider takes audio_path and language
            transcript = provider.transcribe(os.path.join(os.path.dirname(__file__), t["file"]), t["lang"])
            latency = int((time.time() - start) * 1000)
            
            print(f"config status: OK")
            print(f"inference status: OK")
            print(f"provider=BhashiniASRProvider")
            print(f"transcript: {transcript}")
            print(f"latency: {latency}ms")
            
        except Exception as e:
            print(f"Failed: {e}")
            if hasattr(e, 'response'):
                print(f"safe top-level response keys: {list(e.response.json().keys()) if e.response else 'No JSON'}")

if __name__ == "__main__":
    test_asr()
