import os

code = '''from dotenv import load_dotenv
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

# ... [Bhashini health check keeping exactly as before] ...
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
        resp_status = resp.status_code
        if resp.ok:
            data = resp.json()
            endpoint = data.get("pipelineInferenceAPIEndPoint", {})
            return {"status": "ok", "pipeline_config_status": resp_status}
        else:
            return {"status": "error", "pipeline_config_status": resp_status, "error_detail": resp.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/health")
def health_check():
    from providers.factory import is_bhashini_configured
    return {"status": "ok", "voice_service": "available" if is_bhashini_configured() else "not_configured"}

init_db()

# --- Schemas ---

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
    input_mode: str

class TTSRequest(BaseModel):
    language: str
    text: str

# --- Endpoints ---

@app.get("/doctors")
def list_doctors(db: DBSession = Depends(get_db)):
    doctors = db.query(Doctor).all()
    return [{"id": d.id, "name": d.name, "specialty": d.specialty} for d in doctors]

@app.post("/session")
def create_session(data: SessionCreate, db: DBSession = Depends(get_db)):
    # Create or update patient
    patient = db.query(Patient).filter(Patient.abha_id == data.abha_id).first() if data.abha_id else None
    if not patient:
        patient = Patient(name=data.name, age=data.age, gender=data.gender, mobile=data.mobile, abha_id=data.abha_id)
        db.add(patient)
        db.commit()
        db.refresh(patient)
    
    session = PatientSession(patient_id=patient.id, doctor_id=data.doctor_id, language=data.language)
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {"session_id": session.id, "patient_id": patient.id, "status": session.status}

@app.get("/session/{session_id}/next-question")
def get_next_question(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(PatientSession).filter(PatientSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.status == "completed":
        return {"status": "completed"}
        
    history = db.query(HistoryEntry).filter(HistoryEntry.session_id == session_id).order_by(HistoryEntry.id).all()
    
    if not history:
        return {"status": "question", "question": {"text": "Please tap the mic and tell me what symptoms or problems you are facing.", "is_initial": True}}
    
    # Format history
    qa_list = []
    current_q = None
    for h in history:
        if h.role == "assistant":
            current_q = h.content
        elif h.role == "user" and current_q:
            qa_list.append({"question": current_q, "answer": h.content})
            
    initial_symptoms = qa_list[0]["answer"] if qa_list else ""
    
    next_q_text = llm_service.generate_next_questions(initial_symptoms, qa_list)
    
    if next_q_text == "DONE":
        session.status = "completed"
        db.commit()
        return {"status": "completed"}
        
    return {"status": "question", "question": {"text": next_q_text, "is_initial": False}}

@app.post("/session/{session_id}/answer")
def submit_answer(session_id: int, data: AnswerCreate, db: DBSession = Depends(get_db)):
    session = db.query(PatientSession).filter(PatientSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Find the last question asked
    last_q = db.query(HistoryEntry).filter(HistoryEntry.session_id == session_id, HistoryEntry.role == "assistant").order_by(HistoryEntry.id.desc()).first()
    if not last_q and data.answer_raw:
        # If no question was asked (meaning it was the initial prompt)
        db.add(HistoryEntry(session_id=session_id, role="assistant", content="Please tap the mic and tell me what symptoms or problems you are facing."))
        
    ans = HistoryEntry(session_id=session_id, role="user", content=data.answer_raw)
    db.add(ans)
    db.commit()
    
    return {"status": "success"}

@app.post("/session/{session_id}/upload-reports")
async def upload_reports(session_id: int, file: UploadFile = File(...), db: DBSession = Depends(get_db)):
    session = db.query(PatientSession).filter(PatientSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    file_bytes = await file.read()
    extracted_text = ocr_service.extract_text(file_bytes)
    
    doc = Document(session_id=session_id, file_type=file.content_type, extracted_text=extracted_text)
    db.add(doc)
    db.commit()
    
    return {"status": "success", "extracted_text": extracted_text}

@app.post("/session/{session_id}/complete")
def complete_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(PatientSession).filter(PatientSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.status = "completed"
    db.commit()
    
    # Generate summary
    history = db.query(HistoryEntry).filter(HistoryEntry.session_id == session_id).order_by(HistoryEntry.id).all()
    qa_list = []
    current_q = None
    for h in history:
        if h.role == "assistant":
            current_q = h.content
        elif h.role == "user" and current_q:
            qa_list.append({"question": current_q, "answer": h.content})
            
    initial_symptoms = qa_list[0]["answer"] if qa_list else ""
    
    patient_info = {
        "name": session.patient.name,
        "age": session.patient.age,
        "gender": session.patient.gender
    }
    
    docs = db.query(Document).filter(Document.session_id == session_id).all()
    extracted_text = " ".join([d.extracted_text for d in docs if d.extracted_text])
    
    summary_data = llm_service.generate_summary(patient_info, initial_symptoms, qa_list, extracted_text)
    
    consult = Consultation(session_id=session_id, summary_text=json.dumps(summary_data), summary_json=summary_data)
    db.add(consult)
    db.commit()
    
    return {"status": "success"}

@app.get("/session/{session_id}/summary")
def get_session_summary(session_id: int, db: DBSession = Depends(get_db)):
    consult = db.query(Consultation).filter(Consultation.session_id == session_id).first()
    if not consult:
        raise HTTPException(status_code=404, detail="Summary not found")
    return consult.summary_json

@app.get("/doctor/sessions")
def get_doctor_sessions(doctor_id: int, db: DBSession = Depends(get_db)):
    sessions = db.query(PatientSession).filter(PatientSession.doctor_id == doctor_id).all()
    result = []
    for s in sessions:
        consult = db.query(Consultation).filter(Consultation.session_id == s.id).first()
        result.append({
            "session_id": s.id,
            "patient_name": s.patient.name,
            "status": s.status,
            "created_at": s.created_at,
            "summary": consult.summary_json if consult else None
        })
    return result

# --- TTS and ASR logic remaining largely same, just updated request types ---

@app.post("/tts")
def generate_tts(req: TTSRequest):
    import hashlib
    from fastapi.responses import FileResponse, Response
    import requests
    
    if not tts_provider:
        raise HTTPException(status_code=503, detail={"code": "BHASHINI_NOT_CONFIGURED", "message": "Voice services are not configured."})
        
    try:
        audio_bytes = tts_provider.synthesize(req.text, req.language)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Error during TTS processing: {e}")
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
        raise HTTPException(status_code=503, detail="Voice services not configured")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_in:
            temp_in.write(await audio.read())
            temp_in_path = temp_in.name
            
        wav_path = temp_in_path + ".wav"
        
        subprocess.run([
            "ffmpeg", "-y", "-i", temp_in_path, 
            "-ac", "1", "-ar", "16000", wav_path
        ], check=True, capture_output=True)

        text = asr_provider.transcribe(wav_path, language)
        
        processing_ms = int((time.time() - start_time) * 1000)

        return {
            "transcript": text,
            "provider": asr_provider.__class__.__name__,
            "processing_ms": processing_ms
        }

    except Exception as e:
        logger.error(f"Error during ASR processing: {e}")
        raise HTTPException(status_code=500, detail="Internal ASR error")
    finally:
        if "temp_in_path" in locals() and os.path.exists(temp_in_path): os.remove(temp_in_path)
        if "wav_path" in locals() and os.path.exists(wav_path): os.remove(wav_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

with open("backend/main.py", "w") as f:
    f.write(code)
print("main.py rewritten")
