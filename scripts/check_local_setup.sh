#!/bin/bash

# check_local_setup.sh
# Verifies the local environment for MediKiosk development.

set -e

echo "=== Checking Local Setup for MediKiosk ==="

echo "1. Checking Backend..."
if [ ! -f "backend/.env" ]; then
    echo "❌ backend/.env is missing! Creating from .env.example..."
    cp backend/.env.example backend/.env
    echo "✅ backend/.env created. Please update keys (HUGGINGFACE_API_KEY, BHASHINI_API_KEY)."
else
    echo "✅ backend/.env exists."
fi

if ! grep -q "CORS_ORIGINS" backend/.env; then
    echo "❌ CORS_ORIGINS is missing in backend/.env! Adding default for local dev..."
    echo 'CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]' >> backend/.env
else
    echo "✅ CORS_ORIGINS configured."
fi

echo "2. Checking Frontend..."
if [ ! -f "frontend/.env.local" ]; then
    echo "❌ frontend/.env.local is missing! Creating from default..."
    echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > frontend/.env.local
    echo "✅ frontend/.env.local created."
else
    echo "✅ frontend/.env.local exists."
fi

echo "3. Checking Connectivity..."
# Quick check if backend is running
if curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend is running and reachable!"
else
    echo "⚠️ Backend does not appear to be running on localhost:8000 (run: cd backend && uvicorn main:app --reload)"
fi

echo "=== Setup Check Complete ==="
