from abc import ABC, abstractmethod

class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, language: str) -> bytes:
        """
        Returns synthesized audio as bytes. 
        language is 'hi' for Hindi or 'en' for English.
        """
        pass
