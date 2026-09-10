import sys

with open('backend/main.py', 'r') as f:
    content = f.read()

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

# Remove ALL instances
content = content.replace(details_insert, "")

# Now specifically insert it back into get_session_details
target_func = 'def get_session_details(session_id: int, db: DBSession = Depends(get_db)):'
# find the next "return {" after target_func
idx = content.find(target_func)
if idx != -1:
    idx_return = content.find('return {', idx)
    if idx_return != -1:
        content = content[:idx_return] + details_insert[1:] + "\n    " + content[idx_return:]

with open('backend/main.py', 'w') as f:
    f.write(content)
