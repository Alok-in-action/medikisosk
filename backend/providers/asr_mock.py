import time
from .asr_base import ASRProvider

class MockASRProvider(ASRProvider):
    def transcribe(self, audio_path: str, language: str) -> str:
        # Simulate processing delay
        time.sleep(1)
        return "Mujhe teen din se bukhar hai" if language == "hi" else "I have had fever for three days"
