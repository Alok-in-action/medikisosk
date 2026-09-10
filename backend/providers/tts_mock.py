from .tts_base import TTSProvider

class MockTTSProvider(TTSProvider):
    def synthesize(self, text: str, language: str) -> bytes:
        # Return empty bytes for mock TTS
        return b""
