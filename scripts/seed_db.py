import csv
import json
import os
import sys

# Add backend directory to sys.path to import models and database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import init_db, SessionLocal
from backend.models import Question

CSV_PATH = os.path.join(os.path.dirname(__file__), '../data/Medical_Question_Bank_Hackathon-Master Question Bank.csv')

def parse_options(options_str):
    if not options_str:
        return []
    # Split by / or commas, clean whitespace
    return [opt.strip() for opt in options_str.split('/')]

def seed_questions():
    init_db()
    db = SessionLocal()
    
    # Check if already seeded
    if db.query(Question).count() > 0:
        print("Database already seeded. Skipping.")
        db.close()
        return

    questions_added = 0
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        # Skip header rows
        next(reader, None) # title 1
        next(reader, None) # title 2
        next(reader, None) # column headers
        
        for row in reader:
            if not row or not row[0].strip() or not row[0].isdigit():
                continue # Skip empty or category header lines
                
            q_id = int(row[0].strip())
            category = row[1].strip()
            text_en = row[2].strip()
            text_hi = row[3].strip()
            q_type = row[4].strip()
            options_raw = row[5].strip()
            context_note = row[6].strip() if len(row) > 6 else ""
            
            # Simple heuristic for red flags from context notes
            is_red_flag = "red flag" in context_note.lower() or "refer" in context_note.lower()
            red_flag_reason = context_note if is_red_flag else None
            
            q = Question(
                id=q_id,
                category=category,
                text_en=text_en,
                text_hi=text_hi,
                type=q_type,
                options=json.dumps(parse_options(options_raw)),
                red_flag=is_red_flag,
                red_flag_reason=red_flag_reason,
                applies_if=json.dumps([]) # To be filled based on conditionals later
            )
            db.add(q)
            questions_added += 1
            
    db.commit()
    db.close()
    print(f"Successfully seeded {questions_added} questions into the database.")

if __name__ == "__main__":
    seed_questions()
