from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from main import app
from database import get_db, Base, engine
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_session_voice():
    response = client.post(
        "/session",
        json={"language": "hi", "preferred_input_mode": "voice", "consent_given": True}
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert "session_id" in data
    assert data["preferred_input_mode"] == "voice"
    assert data["language"] == "hi"

def test_create_session_touch():
    response = client.post(
        "/session",
        json={"language": "en", "preferred_input_mode": "touch", "consent_given": True}
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert "session_id" in data
    assert data["preferred_input_mode"] == "touch"
    assert data["language"] == "en"

def test_create_session_invalid_mode():
    response = client.post(
        "/session",
        json={"language": "en", "preferred_input_mode": "invalid_mode", "consent_given": True}
    )
    assert response.status_code == 400

def test_get_session():
    # First create one
    post_response = client.post(
        "/session",
        json={"language": "hi", "preferred_input_mode": "voice", "consent_given": True}
    )
    session_id = post_response.json()["session_id"]
    
    # Then get it
    get_response = client.get(f"/session/{session_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["preferred_input_mode"] == "voice"
