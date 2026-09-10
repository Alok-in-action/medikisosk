from abc import ABC, abstractmethod

class ASRProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, language: str) -> str:
        """
        Returns transcribed text. 
        language is 'hi' for Hindi or 'en' for English.
        """
        pass
