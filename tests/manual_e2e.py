import requests
import sqlite3
import time

BASE_URL = "http://localhost:8000"

def run_test():
    print("1. Creating session...")
    resp = requests.post(f"{BASE_URL}/session", json={"language": "hi", "consent_given": True})
    session_id = resp.json()["session_id"]
    print(f"Session ID: {session_id}")
    
    for i in range(4):
        print(f"\nFetching next question (step {i+1})...")
        resp = requests.get(f"{BASE_URL}/session/{session_id}/next-question")
        data = resp.json()
        if data.get("completed"):
            print("Triage completed!")
            break
            
        print(f"Q: {data['text_en']}")
        
        # Mocking an answer
        answer = "I have a fever" if i == 0 else "No"
        print(f"Answering: {answer}")
        
        resp = requests.post(f"{BASE_URL}/session/{session_id}/answer", json={
            "question_id": data["id"],
            "answer_raw": answer,
            "input_mode": "touch"
        })
        print(f"Answer submitted: {resp.json()}")
        time.sleep(0.5)
        
    print("\n--- Verifying Database ---")
    import os
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "medikiosk.db"))
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT question_id, answer_raw FROM answers WHERE session_id = {session_id}")
    rows = cursor.fetchall()
    print("Answers in DB for this session:")
    for r in rows:
        print(f"Question ID: {r[0]}, Answer: {r[1]}")
    conn.close()

if __name__ == "__main__":
    run_test()
