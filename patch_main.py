import sys

with open('backend/main.py', 'r') as f:
    content = f.read()

# 1. Add imports
content = content.replace(
    "from models import Patient, Session as PatientSession, Answer, Question",
    "from models import Patient, Session as PatientSession, Answer, Question, Document, ConsultationRecording\nimport shutil\nimport ocr_service\nfrom datetime import datetime"
)

# 2. Add schemas
schema_insert = """class PatientCreate(BaseModel):
    name: str
    age: int
    sex: str
    mobile: Optional[str] = None
    abha_id: Optional[str] = None

"""
content = content.replace(
    "class SessionCreate(BaseModel):",
    schema_insert + "class SessionCreate(BaseModel):"
)

# 3. Add endpoints before def get_next_question
endpoints = """
@app.post("/patients")
def create_or_get_patient(patient_data: PatientCreate, db: DBSession = Depends(get_db)):
    if patient_data.abha_id:
        p = db.query(Patient).filter(Patient.abha_id == patient_data.abha_id).first()
        if p:
            return {"patient_id": p.id, "status": "existing"}
    if patient_data.mobile:
        p = db.query(Patient).filter(Patient.mobile == patient_data.mobile).first()
        if p:
            return {"patient_id": p.id, "status": "existing"}
            
    p = Patient(
        name=patient_data.name,
        age=patient_data.age,
        sex=patient_data.sex,
        mobile=patient_data.mobile,
        abha_id=patient_data.abha_id
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"patient_id": p.id, "status": "created"}

@app.post("/session/{session_id}/consent")
def submit_consent(session_id: int, db: DBSession = Depends(get_db)):
    s = db.query(PatientSession).filter(PatientSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    s.consent_given = True
    s.consent_timestamp = datetime.utcnow()
    db.commit()
    db.refresh(s)
    return {"status": "success", "consent_timestamp": s.consent_timestamp.isoformat()}

@app.post("/session/{session_id}/reports")
async def upload_report(session_id: int, file: UploadFile = File(...), db: DBSession = Depends(get_db)):
    s = db.query(PatientSession).filter(PatientSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
        
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
        
    upload_dir = f"uploads/{session_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        ocr_result = ocr_service.process_document(file_path, file.filename)
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        ocr_result = {"ocr_status": "failed", "ocr_text": None, "structured": None, "ocr_source": None, "document_type": None}
        
    doc = Document(
        session_id=session_id,
        file_path=file_path,
        file_type=ext,
        original_filename=file.filename,
        ocr_status=ocr_result.get("ocr_status", "completed"),
        ocr_text=ocr_result.get("ocr_text"),
        ocr_json=json.dumps(ocr_result.get("structured")) if ocr_result.get("structured") else None,
        document_type=ocr_result.get("document_type"),
        ocr_source=ocr_result.get("ocr_source")
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    return {
        "document_id": doc.id,
        "ocr_text": doc.ocr_text,
        "structured": json.loads(doc.ocr_json) if doc.ocr_json else None,
        "ocr_source": doc.ocr_source,
        "ocr_status": doc.ocr_status
    }

@app.post("/session/{session_id}/recording")
async def upload_recording(
    session_id: int, 
    file: UploadFile = File(...),
    duration_seconds: Optional[int] = Form(None),
    recorded_by: Optional[str] = Form(None),
    db: DBSession = Depends(get_db)
):
    s = db.query(PatientSession).filter(PatientSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
        
    recording_dir = f"recordings/{session_id}"
    os.makedirs(recording_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = f"{recording_dir}/{timestamp}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    rec = ConsultationRecording(
        session_id=session_id,
        file_path=file_path,
        duration_seconds=duration_seconds,
        recorded_by=recorded_by
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    
    return {
        "recording_id": rec.id,
        "file_path": rec.file_path,
        "recorded_at": rec.recorded_at.isoformat() if rec.recorded_at else None
    }
"""

content = content.replace(
    "@app.post(\"/session\")",
    endpoints + "\n@app.post(\"/session\")"
)

# 4. Update list_sessions patient demographic inclusion
list_replacement = """        result.append({
            "id": s.id,
            "patient_id": s.patient_id,
            "patient_name": s.patient.name if s.patient else None,
            "patient_age": s.patient.age if s.patient else None,
            "patient_sex": s.patient.sex if s.patient else None,
            "status": s.status,
            "consent_given": s.consent_given,
            "created_at": s.created_at.isoformat(),
            "has_red_flags": has_red_flags,
            "verified_status": s.verified_status
        })"""

content = content.replace(
    """        result.append({
            "id": s.id,
            "patient_id": s.patient_id,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
            "has_red_flags": has_red_flags,
            "verified_status": s.verified_status
        })""",
    list_replacement
)

# 5. Update get_session_details 
details_insert = """
    docs = []
    for d in s.documents:
        docs.append({
            "id": d.id,
            "original_filename": d.original_filename,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
            "ocr_status": d.ocr_status,
            "ocr_text": d.ocr_text,
            "structured": json.loads(d.ocr_json) if d.ocr_json else None,
            "ocr_source": d.ocr_source,
            "document_type": d.document_type
        })
        
    recs = []
    for r in s.recordings:
        recs.append({
            "id": r.id,
            "duration_seconds": r.duration_seconds,
            "recorded_by": r.recorded_by,
            "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            "asr_status": r.asr_status,
            "asr_text": r.asr_text
        })
"""

content = content.replace(
    "return {",
    details_insert + "\n    return {"
)

content = content.replace(
    "\"answers\": answers",
    "\"answers\": answers,\n        \"documents\": docs,\n        \"recordings\": recs,\n        \"patient\": {\"name\": s.patient.name, \"age\": s.patient.age, \"sex\": s.patient.sex} if s.patient else None"
)


with open('backend/main.py', 'w') as f:
    f.write(content)

