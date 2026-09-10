import json
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    gender = Column(String)
    mobile = Column(String, index=True, nullable=True)
    abha_id = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="patient")

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    specialty = Column(String)
    email = Column(String, unique=True, index=True, nullable=True)
    password = Column(String, nullable=True)
    
    sessions = relationship("Session", back_populates="doctor")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    language = Column(String)
    status = Column(String, default="active")  # active, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    # Stores the 3 predefined question IDs chosen by Gemini, e.g. [6, 13, 25]
    question_ids = Column(JSON, nullable=True)

    patient = relationship("Patient", back_populates="sessions")
    doctor = relationship("Doctor", back_populates="sessions")
    history_entries = relationship("HistoryEntry", back_populates="session")
    documents = relationship("Document", back_populates="session")
    consultation = relationship("Consultation", back_populates="session", uselist=False)

class HistoryEntry(Base):
    __tablename__ = "history_entries"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    role = Column(String) # system, assistant, user
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="history_entries")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    file_url = Column(String)
    file_type = Column(String) # image, pdf
    extracted_text = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="documents")

class Consultation(Base):
    __tablename__ = "consultations"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), unique=True)
    summary_text = Column(Text)
    summary_json = Column(JSON) 
    recording_url = Column(String, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="consultation")
