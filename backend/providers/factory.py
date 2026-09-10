import os
import logging

logger = logging.getLogger(__name__)

def is_bhashini_configured():
    return bool(os.environ.get("BHASHINI_USER_ID") and os.environ.get("BHASHINI_API_KEY"))

def get_asr_provider():
    if is_bhashini_configured():
        logger.info("ASR provider active: BhashiniASRProvider")
        from .asr_bhashini import BhashiniASRProvider
        return BhashiniASRProvider()
    
    if os.environ.get("USE_MOCK_ASR", "").lower() == "true":
        logger.info("ASR provider active: MockASRProvider")
        from .asr_mock import MockASRProvider
        return MockASRProvider()
        
    logger.info("ASR provider not configured. Voice services unavailable.")
    return None

def get_tts_provider():
    if is_bhashini_configured():
        logger.info("TTS provider active: BhashiniTTSProvider")
        from .tts_bhashini import BhashiniTTSProvider
        return BhashiniTTSProvider()
        
    if os.environ.get("USE_MOCK_TTS", "").lower() == "true":
        logger.info("TTS provider active: MockTTSProvider")
        from .tts_mock import MockTTSProvider
        return MockTTSProvider()
        
    logger.info("TTS provider not configured. Voice services unavailable.")
    return None
