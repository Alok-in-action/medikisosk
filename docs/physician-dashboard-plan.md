# Physician Dashboard Implementation Plan

This plan details the implementation of the Physician Dashboard interface for MediKiosk. The dashboard allows doctors to view completed patient triage sessions and read the generated structured clinical summaries.

## User Review Required

> [!WARNING]
> Please review the design aesthetic and requirements. This dashboard will be built using standard React components with Vanilla CSS or Tailwind (based on the project setup).

## Proposed Changes

### `frontend/src/app/physician/page.tsx`

This will be the main entry point for the physician view.
- **Session List Panel:** A sidebar or left-pane that fetches and lists all completed sessions (displaying Session ID, Patient ID, and time).
- **Summary Detail View:** A main pane that displays the details of the selected session.
- **Red Flag Alerts:** Critical visual indicators (banners or badges) for sessions that have triggered red flags, rendering the `reason` output from the new `check_red_flags` triage engine.

### `backend/main.py`
- We need an endpoint `GET /sessions` to list all sessions so the dashboard can fetch them.
- We already have the endpoint `GET /session/{session_id}/summary` to fetch the structured JSON summary for a selected session.

#### [NEW] `backend/main.py`
We will add:
```python
@app.get("/sessions")
def list_sessions(db: DBSession = Depends(get_db)):
    # Returns a list of all sessions, optionally filtered by status="completed"
    ...
```

#### [NEW] `frontend/src/app/physician/page.tsx`
We will create the React component to fetch the `/sessions` and display the dashboard.

## Verification Plan

### Manual Verification
1. Open the physician dashboard URL (`http://localhost:3000/physician`).
2. Verify that the session created during the manual E2E test appears in the list.
3. Click on the session and verify that the structured JSON summary (Chief Complaint, HPI, Red Flags) is rendered cleanly in the UI.
