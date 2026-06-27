#!/bin/bash
# 🚀 CryptoPulse Lightweight Pipeline Runner
# This script runs the entire pipeline end-to-end on a resource-constrained Linux machine.

set -e # Exit immediately if a command exits with a non-zero status

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "============================================================"
echo "   🚀 CryptoPulse Lightweight Pipeline Runner"
echo "============================================================"

step=$1

if [ -z "$step" ] || [ "$step" == "all" ]; then
    run_all=true
else
    run_all=false
fi

# ── Step 1: Install Requirements ──
if [ "$run_all" = true ] || [ "$step" == "install" ]; then
    echo -e "\n📦 [1/6] Installing Python Requirements..."
    pip install -r req_main.txt
fi

# ── Step 2: Setup Database Schema ──
if [ "$run_all" = true ] || [ "$step" == "schema" ]; then
    echo -e "\n🔧 [2/6] Setting up Supabase Schema..."
    python scripts/setup_supabase_schema.py
fi

# ── Step 3: Seed Silver Layer ──
if [ "$run_all" = true ] || [ "$step" == "seed" ]; then
    echo -e "\n🌱 [3/6] Seeding Silver Layer Data..."
    python scripts/seed_supabase_direct.py
fi

# ── Step 4: Run dbt (Silver -> Gold) ──
if [ "$run_all" = true ] || [ "$step" == "dbt" ]; then
    echo -e "\n🏗️ [4/6] Running dbt (Building Gold Layer)..."
    cd processing/dbt
    # Ensure dbt is installed
    pip install dbt-core==1.7.0 dbt-postgres==1.7.0
    dbt deps
    dbt run
    echo -e "\n✅ Running dbt tests..."
    dbt test || echo "⚠️ dbt tests failed, but starting servers anyway..."
    cd ../..
fi

# ── Step 5: Start Backend (FastAPI) ──
if [ "$step" == "backend" ] || [ "$step" == "start" ]; then
    echo -e "\n⚙️ [5/6] Starting FastAPI Backend..."
    cd backend
    if [ -d "../venv" ]; then
        source ../venv/bin/activate
    fi
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    if [ -d "../venv" ]; then
        deactivate
    fi
    cd ..
fi

# ── Step 6: Start Frontend (Next.js) ──
if [ "$step" == "frontend" ] || [ "$step" == "start" ]; then
    echo -e "\n🌐 [6/6] Starting Next.js Frontend..."
    cd frontend
    npm install --legacy-peer-deps
    npm run dev &
    FRONTEND_PID=$!
    cd ..
fi

if [ "$step" == "start" ]; then
    echo -e "\n✅ Backend running on PID $BACKEND_PID (http://localhost:8000)"
    echo -e "✅ Frontend running on PID $FRONTEND_PID (http://localhost:3000)"
    
    # 🌐 Automatically open default Windows host browser
    echo -e "\n🌐 Opening Next.js Frontend in your default browser..."
    explorer.exe "http://localhost:3000" 2>/dev/null || cmd.exe /c start "http://localhost:3000" 2>/dev/null || true

    echo -e "\n🛑 Press Ctrl+C to stop both servers."
    wait $BACKEND_PID $FRONTEND_PID
elif [ "$run_all" = true ]; then
    echo -e "\n🎉 Pipeline execution complete! To start the servers, run:"
    echo "  ./scripts/run_pipeline.sh start"
fi
