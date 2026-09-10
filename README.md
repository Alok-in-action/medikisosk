# MediKiosk

AI-powered clinical triage kiosk.

## Local Development Setup

To verify your local environment is correctly configured for both the backend and frontend, run the setup check script:

```bash
./scripts/check_local_setup.sh
```

### Backend
1. Ensure `.env` is populated with `HUGGINGFACE_API_KEY`, `BHASHINI_API_KEY`, and `CORS_ORIGINS`.
2. Install dependencies: `cd backend && pip install -r requirements.txt`
3. Run: `cd backend && uvicorn main:app --reload`

### Frontend
1. Ensure `.env.local` contains `NEXT_PUBLIC_API_BASE_URL` pointing to the backend.
2. Install dependencies: `cd frontend && npm install`
3. Run: `cd frontend && npm run dev`
