from sqlalchemy.orm import Session
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal
from models import Question

db = SessionLocal()
if not db.query(Question).filter(Question.id == 220).first():
    q = Question(
        id=220,
        category="Fever",
        text_en="Did you measure your temperature?",
        text_hi="क्या आपने अपना तापमान मापा था?",
        type="single_choice",
        options=json.dumps(["Yes, I know the reading", "Yes, but I do not remember", "No, I did not measure it", "I am not sure"]),
        red_flag=False,
        applies_if=json.dumps([])
    )
    db.add(q)
    db.commit()
    print("Added Q220.")
else:
    print("Q220 already exists.")
db.close()
