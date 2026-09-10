import os
import sys
import logging

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)

def seed_demo_sessions():
    logger.info("Seeding emergency demo session...")
    # Create emergency session (Hindi)
    res = client.post("/session", json={"language": "hi", "consent_given": True})
    emergency_session_id = res.json()["session_id"]
    
    # Q1: Chief Complaint (Fever and Cough)
    client.post(f"/session/{emergency_session_id}/answer", json={
        "question_id": 1,
        "answer_raw": "बुखार और खांसी",
        "input_mode": "voice"
    })
    
    # Q2: Duration
    client.post(f"/session/{emergency_session_id}/answer", json={
        "question_id": 2,
        "answer_raw": "5 दिन",
        "input_mode": "voice"
    })
    
    # Q42: Cough duration
    client.post(f"/session/{emergency_session_id}/answer", json={
        "question_id": 42,
        "answer_raw": "5 दिन",
        "input_mode": "voice"
    })
    
    # Q43: Blood in sputum (Red Flag Trigger)
    client.post(f"/session/{emergency_session_id}/answer", json={
        "question_id": 43,
        "answer_raw": "हाँ, खून आ रहा है",
        "input_mode": "voice"
    })
    
    # Complete the session by answering the next question negatively if asked, or just let the engine wrap up
    # We will just fetch next questions and say no to them until completion to trigger summary
    while True:
        next_res = client.get(f"/session/{emergency_session_id}/next-question")
        data = next_res.json()
        if data.get("completed"):
            break
        q_id = data["id"]
        client.post(f"/session/{emergency_session_id}/answer", json={
            "question_id": q_id,
            "answer_raw": "नहीं",
            "input_mode": "touch"
        })
        
    logger.info(f"Emergency session {emergency_session_id} seeded successfully.")

    logger.info("Seeding normal demo session...")
    # Create normal session (Hindi)
    res2 = client.post("/session", json={"language": "hi", "consent_given": True})
    normal_session_id = res2.json()["session_id"]
    
    # Q1: Chief Complaint
    client.post(f"/session/{normal_session_id}/answer", json={
        "question_id": 1,
        "answer_raw": "खांसी",
        "input_mode": "touch"
    })
    
    # Q42: Cough duration
    client.post(f"/session/{normal_session_id}/answer", json={
        "question_id": 42,
        "answer_raw": "2 दिन",
        "input_mode": "touch"
    })
    
    # Q43: Blood in sputum (No)
    client.post(f"/session/{normal_session_id}/answer", json={
        "question_id": 43,
        "answer_raw": "नहीं",
        "input_mode": "touch"
    })
    
    while True:
        next_res = client.get(f"/session/{normal_session_id}/next-question")
        data = next_res.json()
        if data.get("completed"):
            break
        q_id = data["id"]
        client.post(f"/session/{normal_session_id}/answer", json={
            "question_id": q_id,
            "answer_raw": "नहीं",
            "input_mode": "touch"
        })
        
    logger.info(f"Normal session {normal_session_id} seeded successfully.")

if __name__ == "__main__":
    seed_demo_sessions()
