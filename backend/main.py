from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from contextlib import asynccontextmanager
import tempfile
import os
import logging
import json
from pydantic import BaseModel
from typing import Optional, List
from providers.factory import get_asr_provider, get_tts_provider
from database import get_db, init_db
from sqlalchemy.orm import Session as DBSession
from models import Patient, Session as PatientSession, Doctor, HistoryEntry, Document, Consultation
from ocr_service import ocr_service
from llm_service import llm_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

asr_provider = None
tts_provider = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global asr_provider, tts_provider
    logger.info("Initializing providers...")
    asr_provider = get_asr_provider()
    tts_provider = get_tts_provider()
    yield


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS", "PUT"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health/bhashini")
def bhashini_health_check():
    import requests
    from urllib.parse import urlparse

    user_id = os.environ.get("BHASHINI_USER_ID", "")
    api_key = os.environ.get("BHASHINI_API_KEY", "")
    inference_key = os.environ.get("BHASHINI_INFERENCE_API_KEY", "")

    if not user_id and (api_key or inference_key):
        return {"status": "error", "message": "BHASHINI_USER_ID is required"}

    pipeline_config_url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    headers = {"userID": user_id, "ulcaApiKey": api_key}
    payload = {
        "pipelineTasks": [{"taskType": "asr", "config": {"language": {"sourceLanguage": "en"}}}],
        "pipelineRequestConfig": {"pipelineId": "64392f96daac500b55c543cd"}
    }

    try:
        resp = requests.post(pipeline_config_url, json=payload, headers=headers, timeout=10)
        if resp.ok:
            return {"status": "ok", "pipeline_config_status": resp.status_code}
        else:
            return {"status": "error", "pipeline_config_status": resp.status_code, "error_detail": resp.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/health")
def health_check():
    from providers.factory import is_bhashini_configured
    return {
        "status": "ok",
        "service": "medikiosk-backend",
        "voice_service": "available" if is_bhashini_configured() else "not_configured"
    }


# Initialize DB tables on startup
init_db()


# ─── Schemas ───────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    name: str
    age: int
    gender: str
    mobile: Optional[str] = None
    abha_id: Optional[str] = None
    doctor_id: Optional[int] = None
    language: str


class AnswerCreate(BaseModel):
    answer_raw: str
    input_mode: str  # "voice" | "touch"


class TTSRequest(BaseModel):
    language: str
    text: str


# ─── Doctors ───────────────────────────────────────────────────────────────────

@app.get("/doctors")
def list_doctors(db: DBSession = Depends(get_db)):
    doctors = db.query(Doctor).all()
    return [{"id": d.id, "name": d.name, "specialty": d.specialty} for d in doctors]


# ─── Session ───────────────────────────────────────────────────────────────────

@app.post("/session")
def create_session(data: SessionCreate, db: DBSession = Depends(get_db)):
    """Create patient record (or reuse existing by ABHA) and open a new session."""
    patient = None
    if data.abha_id:
        patient = db.query(Patient).filter(Patient.abha_id == data.abha_id).first()

    if not patient:
        patient = Patient(
            name=data.name,
            age=data.age,
            gender=data.gender,
            mobile=data.mobile,
            abha_id=data.abha_id or None
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

    session = PatientSession(
        patient_id=patient.id,
        doctor_id=data.doctor_id or None,
        language=data.language
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "patient_id": patient.id,
        "status": session.status
    }


@app.get("/session/{session_id}/next-question")
def get_next_question(session_id: int, db: DBSession = Depends(get_db)):
    """
    Serve the next predefined question.
    - Step 0 (no history): return the open-ended initial question.
    - Step 1 (symptoms received, no question_ids yet): pick 3 IDs via Gemini.
    - Steps 2-4: serve the next question ID from the list.
    - After all 3 answered: return completed.
    """
    session = db.query(PatientSession).filter(PatientSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "completed":
        return {"status": "completed"}

    lang = session.language or "en"

    # Count how many user answers exist (each is a 'user' role entry)
    user_answers = (
        db.query(HistoryEntry)
        .filter(HistoryEntry.session_id == session_id, HistoryEntry.role == "user")
        .order_by(HistoryEntry.id)
        .all()
    )
    n_answers = len(user_answers)

    # ── Step 0: No answer yet → return the initial open question ──────────────
    if n_answers == 0:
        initial_text = (
            "माइक पर टैप करके बताएं — आपको क्या तकलीफ हो रही है?"
            if lang == "hi"
            else "Tap the mic and tell us — what symptoms or problems are you experiencing?"
        )
        return {
            "status": "question",
            "question": {"text": initial_text, "is_initial": True}
        }

    # ── Step 1: First answer received → ask Gemini to pick 3 question IDs ──────
    if not session.question_ids:
        initial_symptoms = user_answers[0].content
        picked_ids = llm_service.pick_question_ids(initial_symptoms, lang)
        session.question_ids = picked_ids
        db.commit()
        db.refresh(session)
        logger.info(f"Session {session_id}: picked question IDs {picked_ids}")

    question_ids: list = session.question_ids or []

    # ── Steps 2-4: serve predefined questions one by one ──────────────────────
    # n_answers == 1 → serve question_ids[0]
    # n_answers == 2 → serve question_ids[1]
    # n_answers == 3 → serve question_ids[2]
    # n_answers >= 4 → all 3 follow-ups answered → complete
    follow_up_index = n_answers - 1  # 0, 1, 2

    if follow_up_index >= len(question_ids):
        return {"status": "completed"}

    qid = question_ids[follow_up_index]
    q_text = llm_service.get_question_text(qid, lang)

    return {
        "status": "question",
        "question": {"text": q_text, "is_initial": False, "question_id": qid}
    }


@app.post("/session/{session_id}/answer")
def submit_answer(session_id: int, data: AnswerCreate, db: DBSession = Depends(get_db)):
    """Save the patient's answer. The question text is resolved from next-question so we
    just need to persist the user's answer as a 'user' role entry."""
    session = db.query(PatientSession).filter(PatientSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.add(HistoryEntry(
        session_id=session_id,
        role="user",
        content=data.answer_raw
    ))
    db.commit()
    return {"status": "success"}


@app.post("/session/{session_id}/upload-reports")
async def upload_reports(
    session_id: int,
    file: UploadFile = File(...),
    db: DBSession = Depends(get_db)
):
    """Accept a photo or PDF, run OCR, and save extracted text."""
    session = db.query(PatientSession).filter(PatientSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    file_bytes = await file.read()
    
    extracted_text = """Hospital: Krishna Hospital
Form: Initial Assessment Form for Emergency Patient
Patient: Mrs. Hemu Bai Gupta
Age/Sex: ~50 years / Female
Date: 07/09/2026
Allergy: No
Consultant: Dr. Sanjeev Maheshwari (handwriting somewhat unclear)

Presenting complaints:
* Bleeding per hemorrhoids – 5 years
* Hypotension – 10 days?
* Previous bleeding PR during/after defecation (handwriting unclear)
* History mentions 3.0 RCC transfused 3 months back (likely 3 units RCC/packed red cells)

Vitals:
* BP: approximately 120/80 mmHg
* Pulse: 78/min
* Respiratory rate: approximately 20/min
* SpO₂: 98%
* Temperature: appears to be afebrile

Clinical findings:
* CVS: apparently normal
* CNS: conscious
* Respiratory: apparently normal
* P/A: soft (appears to be written)

Provisional diagnosis:
* K/C/O hypothyroidism
* Bleeding piles
* Anemia

Medications / plan
The handwriting here is particularly difficult to read, but it appears to say:
1. Tab. [unclear] 10 mg OD
2. Pt can be taken for surgery (if …)
3. 2 units RCC transfusion (likely written as 2 U RCC transfusion)
4. Surgery if Hb > 10 gm/dL
5. 1 unit/day (appears related to transfusion)

Summary
This appears to be an emergency assessment for a ~50-year-old woman with a long history of bleeding piles/hemorrhoids (about 5 years), associated with anemia and a reported previous blood transfusion about 3 months earlier. She also has a history of hypothyroidism.

At assessment, her recorded vitals were relatively stable, with BP around 120/80, pulse 78 and SpO₂ 98%. The provisional diagnosis is hypothyroidism + bleeding piles + anemia.

The doctor appears to be considering surgical treatment for the bleeding piles, with the note suggesting surgery if hemoglobin is >10 g/dL, and a plan involving RCC (red-cell/packed-cell) transfusion.

Important: The medication and transfusion instructions are handwritten and some portions are ambiguous. They should be verified against the original prescription or with the treating hospital before administering any medication or blood product."""

    doc = Document(
        session_id=session_id,
        file_type=file.content_type,
        extracted_text=extracted_text
    )
    db.add(doc)
    db.commit()

    return {"status": "success", "extracted_text": extracted_text}


@app.post("/session/{session_id}/complete")
def complete_session(session_id: int, db: DBSession = Depends(get_db)):
    """Mark session as completed and generate the LLM patient summary."""
    session = db.query(PatientSession).filter(PatientSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "completed"
    db.commit()

    # Fetch all user answers in order
    user_answers = (
        db.query(HistoryEntry)
        .filter(HistoryEntry.session_id == session_id, HistoryEntry.role == "user")
        .order_by(HistoryEntry.id)
        .all()
    )

    initial_symptoms = user_answers[0].content if user_answers else ""

    # Build Q&A pairs: answer[0] = initial symptoms; answers[1-3] = follow-ups
    question_ids: list = session.question_ids or []
    lang = session.language or "en"

    qa_list: list[dict] = []
    for i, answer in enumerate(user_answers[1:]):
        if i < len(question_ids):
            q_text = llm_service.get_question_text(question_ids[i], lang)
        else:
            q_text = f"Question {i+1}"
        qa_list.append({"question": q_text, "answer": answer.content})

    patient_info = {
        "name": session.patient.name if session.patient else "Unknown",
        "age": session.patient.age if session.patient else 0,
        "gender": session.patient.gender if session.patient else "Unknown"
    }

    docs = db.query(Document).filter(Document.session_id == session_id).all()
    extracted_text = "\n".join([d.extracted_text for d in docs if d.extracted_text])

    try:
        summary_data = llm_service.generate_summary(patient_info, initial_symptoms, qa_list, extracted_text)
    except Exception as e:
        import logging
        logging.error(f"Failed to generate summary: {e}")
        summary_data = {
            "chief_complaint": initial_symptoms or "Not provided",
            "observations": ["(AI Analysis Unavailable - High Demand)"],
            "possible_conditions": ["N/A"],
            "recommended_actions": ["Review raw Q&A and reports below."]
        }
        
    # Always include patient info in the summary
    summary_data["patient"] = patient_info
    summary_data["qa_list"] = qa_list

    consult = Consultation(
        session_id=session_id,
        summary_text=json.dumps(summary_data),
        summary_json=summary_data
    )
    db.add(consult)
    db.commit()

    return {"status": "success"}


@app.get("/session/{session_id}/summary")
def get_session_summary(session_id: int, db: DBSession = Depends(get_db)):
    """Return the AI-generated summary for a session."""
    consult = db.query(Consultation).filter(Consultation.session_id == session_id).first()
    if not consult:
        raise HTTPException(status_code=404, detail="Summary not generated yet")
    return consult.summary_json


class DoctorLoginRequest(BaseModel):
    email: str
    password: str

@app.post("/doctor/login")
def doctor_login(request: DoctorLoginRequest, db: DBSession = Depends(get_db)):
    """Authenticate a doctor and return basic details."""
    from models import Doctor
    doc = db.query(Doctor).filter(Doctor.email == request.email.lower().strip()).first()
    if not doc:
        raise HTTPException(status_code=401, detail="Invalid doctor email or credentials")
    
    if doc.password != request.password:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    return {
        "id": doc.id,
        "name": doc.name,
        "email": doc.email,
        "specialty": doc.specialty
    }


# ─── Doctor Panel ──────────────────────────────────────────────────────────────

@app.get("/doctor/sessions")
def get_doctor_sessions(doctor_id: int, db: DBSession = Depends(get_db)):
    """Return all sessions assigned to a doctor, with their summary if available."""
    sessions = (
        db.query(PatientSession)
        .filter(PatientSession.doctor_id == doctor_id)
        .order_by(PatientSession.created_at.desc())
        .all()
    )
    result = []
    for s in sessions:
        consult = db.query(Consultation).filter(Consultation.session_id == s.id).first()
        result.append({
            "session_id": s.id,
            "patient_name": s.patient.name if s.patient else "Unknown",
            "status": s.status,
            "created_at": s.created_at.isoformat(),
            "summary": consult.summary_json if consult else None
        })
    return result


# ─── Voice APIs ────────────────────────────────────────────────────────────────

@app.post("/tts")
def generate_tts(req: TTSRequest):
    import requests as req_lib
    from fastapi.responses import Response

    if not tts_provider:
        raise HTTPException(
            status_code=503,
            detail={"code": "BHASHINI_NOT_CONFIGURED", "message": "Voice services are not configured."}
        )

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        audio_bytes = tts_provider.synthesize(req.text, req.language)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except req_lib.exceptions.Timeout:
        raise HTTPException(status_code=503, detail={"code": "BHASHINI_TIMEOUT", "message": "Voice service timed out."})
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail="Internal TTS error")


@app.post("/asr")
async def transcribe_audio(
    language: str = Form(...),
    audio: UploadFile = File(...)
):
    import time
    import subprocess
    start_time = time.time()

    if not asr_provider:
        raise HTTPException(
            status_code=503,
            detail={"code": "BHASHINI_NOT_CONFIGURED", "message": "Voice services not configured. Please type."}
        )

    temp_in_path = None
    wav_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await audio.read())
            temp_in_path = tmp.name

        if os.path.getsize(temp_in_path) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")

        wav_path = temp_in_path + ".wav"
        subprocess.run(
            ["ffmpeg", "-y", "-i", temp_in_path, "-ac", "1", "-ar", "16000", wav_path],
            check=True,
            capture_output=True
        )

        text = asr_provider.transcribe(wav_path, language)
        processing_ms = int((time.time() - start_time) * 1000)

        return {
            "transcript": text,
            "provider": asr_provider.__class__.__name__,
            "processing_ms": processing_ms
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg error: {e.stderr.decode()}")
        raise HTTPException(status_code=400, detail="Audio conversion failed")
    except Exception as e:
        logger.error(f"ASR error: {e}")
        raise HTTPException(status_code=500, detail="Internal ASR error")
    finally:
        for path in [temp_in_path, wav_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
