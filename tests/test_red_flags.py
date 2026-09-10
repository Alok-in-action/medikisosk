import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Patient, Session, Answer, Question
from logic import TriageEngine

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_q43_yes_emergency_haemoptysis(db_session):
    engine = TriageEngine(db_session)
    alert = engine.check_red_flags(43, "yes", [])
    assert alert is not None
    assert alert["severity"] == "emergency"
    assert "haemoptysis" in alert["reason"]

def test_q43_no_produces_no_alert(db_session):
    engine = TriageEngine(db_session)
    alert = engine.check_red_flags(43, "no", [])
    assert alert is None

def test_q44_at_rest_emergency(db_session):
    engine = TriageEngine(db_session)
    alert = engine.check_red_flags(44, "at rest", [])
    assert alert is not None
    assert alert["severity"] == "emergency"
    assert "rest" in alert["reason"]

def test_q55_yes_urgent(db_session):
    engine = TriageEngine(db_session)
    alert = engine.check_red_flags(55, "yes", [])
    assert alert is not None
    assert alert["severity"] == "urgent"

def test_q88_yes_emergency(db_session):
    engine = TriageEngine(db_session)
    alert = engine.check_red_flags(88, "yes", [])
    assert alert is not None
    assert alert["severity"] == "emergency"

def test_q94_yes_emergency(db_session):
    engine = TriageEngine(db_session)
    alert = engine.check_red_flags(94, "yes", [])
    assert alert is not None
    assert alert["severity"] == "emergency"

def test_dengue_warning_combo(db_session):
    engine = TriageEngine(db_session)
    
    # 1. Chief Complaint: Fever
    q1_answer = Answer(question_id=1, answer_raw="I have a fever")
    
    # 2. Q26 (Rash with fever) = yes
    q26_answer = Answer(question_id=26, answer_raw="yes")
    
    # We are now answering Q30 (Pain behind eyes)
    session_answers = [q1_answer, q26_answer]
    
    alert = engine.check_red_flags(30, "yes", session_answers)
    assert alert is not None
    assert alert["severity"] == "urgent"
    assert "Dengue" in alert["reason"]
    
    # What if answering Q26 second?
    q30_answer = Answer(question_id=30, answer_raw="yes")
    session_answers_2 = [q1_answer, q30_answer]
    alert2 = engine.check_red_flags(26, "yes", session_answers_2)
    assert alert2 is not None
    assert alert2["severity"] == "urgent"
    assert "Dengue" in alert2["reason"]

def test_negative_answers_do_not_create_false_alerts(db_session):
    engine = TriageEngine(db_session)
    
    assert engine.check_red_flags(20, "no", []) is None
    assert engine.check_red_flags(44, "with exertion", []) is None
    assert engine.check_red_flags(47, "no", []) is None
    assert engine.check_red_flags(55, "never", []) is None
    assert engine.check_red_flags(59, "nope", []) is None
    assert engine.check_red_flags(63, "nah", []) is None
    
    # Fever combo test with negative answer
    q1_answer = Answer(question_id=1, answer_raw="I have a fever")
    q26_answer = Answer(question_id=26, answer_raw="no")
    alert = engine.check_red_flags(30, "no", [q1_answer, q26_answer])
    assert alert is None
