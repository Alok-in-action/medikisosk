import os
import pytest
from backend.providers.factory import get_asr_provider
from backend.providers.asr_bhashini import BhashiniASRProvider
from backend.providers.asr_ai4bharat import AI4BharatASRProvider
from backend.providers.asr_mock import MockASRProvider

@pytest.fixture
def clean_env():
    # Remove variables if they exist
    for key in ["BHASHINI_USER_ID", "BHASHINI_API_KEY", "USE_MOCK_ASR"]:
        if key in os.environ:
            del os.environ[key]
    yield
    # Cleanup after test
    for key in ["BHASHINI_USER_ID", "BHASHINI_API_KEY", "USE_MOCK_ASR"]:
        if key in os.environ:
            del os.environ[key]

def test_bhashini_provider_active_when_keys_present(clean_env):
    os.environ["BHASHINI_USER_ID"] = "test_user"
    os.environ["BHASHINI_API_KEY"] = "test_key"
    
    provider = get_asr_provider()
    assert isinstance(provider, BhashiniASRProvider)

def test_mock_provider_active(clean_env):
    os.environ["USE_MOCK_ASR"] = "true"
    
    provider = get_asr_provider()
    assert isinstance(provider, MockASRProvider)

def test_ai4bharat_provider_default(clean_env):
    # No keys set
    provider = get_asr_provider()
    assert isinstance(provider, AI4BharatASRProvider)
