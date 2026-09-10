import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add backend to path so we can import from it
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from main import app
from database import get_db, Base, engine
from sqlalchemy.orm import sessionmaker

# Set up test database
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_create_session_with_voice_preference():
    response = client.post(
        "/session",
        json={"language": "en", "consent_given": True, "preferred_input_mode": "voice"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    session_id = data["session_id"]
    
    # Retrieve it
    response = client.get(f"/session/{session_id}")
    assert response.status_code == 200
    assert response.json()["preferred_input_mode"] == "voice"

def test_create_session_with_touch_preference():
    response = client.post(
        "/session",
        json={"language": "hi", "consent_given": True, "preferred_input_mode": "touch"}
    )
    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]
    
    # Retrieve it
    response = client.get(f"/session/{session_id}")
    assert response.status_code == 200
    assert response.json()["preferred_input_mode"] == "touch"

def test_create_session_invalid_preference():
    response = client.post(
        "/session",
        json={"language": "hi", "consent_given": True, "preferred_input_mode": "brainwave"}
    )
    assert response.status_code == 400

def test_patch_preference():
    response = client.post(
        "/session",
        json={"language": "en", "consent_given": True, "preferred_input_mode": "voice"}
    )
    session_id = response.json()["session_id"]
    
    response = client.patch(
        f"/session/{session_id}/preference",
        json={"preferred_input_mode": "touch"}
    )
    assert response.status_code == 200
    assert response.json()["preferred_input_mode"] == "touch"
    
    # Verify persistence
    response = client.get(f"/session/{session_id}")
    assert response.json()["preferred_input_mode"] == "touch"

def test_patch_invalid_preference():
    response = client.post(
        "/session",
        json={"language": "en", "consent_given": True, "preferred_input_mode": "voice"}
    )
    session_id = response.json()["session_id"]
    
    response = client.patch(
        f"/session/{session_id}/preference",
        json={"preferred_input_mode": "invalid"}
    )
    assert response.status_code == 400
