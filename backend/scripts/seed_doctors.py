import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import Doctor

def seed_doctors():
    db = SessionLocal()
    doctors = [
        {"name": "Dr. Shubh Jain", "specialty": "General Medicine", "email": "shubh@gmail.com", "password": "shubh@123"},
        {"name": "Dr. Alok Khamora", "specialty": "Pediatrics", "email": "alok@gmail.com", "password": "alok@123"},
        {"name": "Dr. Riya Rathore", "specialty": "Dermatology", "email": "riya@gmail.com", "password": "riya@123"},
        {"name": "Dr. Ankit Gupta", "specialty": "Neurology", "email": "ankit@gmail.com", "password": "ankit@123"},
        {"name": "Dr. Anshul Sethiya", "specialty": "Psychiatry", "email": "anshul@gmail.com", "password": "anshul@123"},
        {"name": "Dr. Sneha Chouhan", "specialty": "Cardiology", "email": "sneha@gmail.com", "password": "sneha@123"},
    ]
    
    for doc in doctors:
        existing = db.query(Doctor).filter(Doctor.name == doc["name"]).first()
        if not existing:
            new_doc = Doctor(name=doc["name"], specialty=doc["specialty"], email=doc["email"], password=doc["password"])
            db.add(new_doc)
        else:
            existing.email = doc["email"]
            existing.password = doc["password"]
            
    db.commit()
    db.close()
    print("Doctors seeded successfully.")

if __name__ == "__main__":
    seed_doctors()
