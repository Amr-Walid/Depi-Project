#!/bin/bash
# 🚀 CryptoPulse Sequential Spark Pipeline Runner
# This script orchestrates the actual Spark/Kafka pipeline sequentially
# so it can run successfully on a resource-constrained Linux machine without crashing.

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "============================================================"
echo "   🚀 CryptoPulse Sequential Spark Pipeline"
echo "============================================================"

# Helper function to run a background Python process with a timeout
run_with_timeout() {
    local cmd=$1
    local duration=$2
    local name=$3

    echo "▶️  Running $name for $duration seconds..."
    # Run the command in the background
    $cmd &
    local pid=$!
    
    # Wait for the specified duration
    sleep $duration
    
    # Kill the process
    echo "⏹️  Stopping $name (PID: $pid)..."
    kill -15 $pid 2>/dev/null || true
    wait $pid 2>/dev/null || true
    echo "✅ $name data collection complete."
}

# ── 1. Start Infrastructure ──
echo -e "\n🐳 [1/7] Starting Infrastructure (Kafka, Zookeeper, Postgres)..."
docker compose up -d zookeeper kafka kafka-init-topics postgres
echo "Waiting for Kafka to be fully ready (30 seconds)..."
sleep 30

# ── 2. Collect Real Data (Producers) ──
echo -e "\n📡 [2/7] Collecting Real Data into Kafka..."

# Setup python virtual environment and lightweight dependencies
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "📦 Installing required Python dependencies (fast, no PySpark)..."
pip install -q kafka-python websocket-client requests feedparser psycopg2-binary python-dotenv dbt-postgres fastapi uvicorn supabase pydantic --break-system-packages

# Run Binance Producer for 45 seconds to collect a batch of prices
run_with_timeout "python ingestion/producers/producer_binance.py" 45 "Binance Real-time Prices"

# Run News Producer for 30 seconds
run_with_timeout "python ingestion/producers/producer_news.py" 30 "Crypto News"

# Run Social Producer for 30 seconds
run_with_timeout "python ingestion/producers/producer_social_rss.py" 30 "Social RSS"

# Fetch Historical Data (Batch, no timeout needed as it exits on its own)
echo "▶️  Fetching Historical Data..."
python ingestion/historical/historical_fetcher.py
echo "✅ Historical data collection complete."


# ── 3. Start Spark Cluster ──
echo -e "\n🔥 [3/7] Starting Spark Cluster..."
docker compose up -d spark-master spark-worker
echo "Waiting for Spark to initialize (15 seconds)..."
sleep 15


# ── 4. Process Data (Bronze -> Silver -> Sync) Sequentially ──
echo -e "\n⚙️ [4/7] Running Spark Jobs Sequentially..."

run_spark_job() {
    local script=$1
    local name=$2
    echo "  ▶️  Running $name..."
    docker exec spark-master /opt/spark/bin/spark-submit /opt/spark/jobs/$script
    echo "  ✅ $name finished."
}

# Real-time Prices Pipeline
echo -e "\n--- Processing Prices ---"
run_spark_job "bronze_consumer.py" "Bronze Prices (Kafka -> ADLS)"
run_spark_job "silver_prices_processor.py" "Silver Prices (Clean & Upsert)"
run_spark_job "sync_prices_pg.py" "Sync Prices to Postgres"

# News Pipeline
echo -e "\n--- Processing News ---"
run_spark_job "bronze_news_consumer.py" "Bronze News (Kafka -> ADLS)"
run_spark_job "silver_news_processor.py" "Silver News (Clean)"
run_spark_job "sync_news_pg.py" "Sync News to Postgres"

# Social Pipeline
echo -e "\n--- Processing Social ---"
run_spark_job "bronze_social_consumer.py" "Bronze Social (Kafka -> ADLS)"
run_spark_job "silver_social_processor.py" "Silver Social (Clean)"
run_spark_job "sync_social_pg.py" "Sync Social to Postgres"

# Historical Pipeline
echo -e "\n--- Processing Historical ---"
run_spark_job "historical_loader.py" "Bronze Historical (JSON -> ADLS)"
run_spark_job "silver_historical_processor.py" "Silver Historical (Clean)"
run_spark_job "sync_historical_pg.py" "Sync Historical to Postgres"


# ── 5. Inject Simulated Sentiment ──
echo -e "\n🧠 [5/7] Injecting Simulated Sentiment (Skipping heavy FinBERT)..."
# We use our lightweight python seeder to just inject the simulated sentiment into Postgres
python -c "
import sys
sys.path.append('scripts')
from seed_supabase_direct import seed_sentiment, get_connection
conn = get_connection()
seed_sentiment(conn)
conn.close()
"


# ── 6. Shutdown Heavy Infrastructure ──
echo -e "\n🛑 [6/7] Stopping Spark and Kafka to free up RAM..."
docker compose stop spark-master spark-worker zookeeper kafka kafka-init-topics


# ── 7. Run dbt and Start Web Servers ──
echo -e "\n🏗️ [7/7] Running dbt and Starting Web Apps..."

# Run dbt
cd processing/dbt
dbt deps
dbt run
dbt test
cd ../..

# Start Backend
echo -e "\n⚙️  Starting FastAPI Backend..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Start Frontend
echo -e "\n🌐  Starting Next.js Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "\n🎉 Pipeline execution complete! Servers are starting up."
echo -e "✅ Backend running on PID $BACKEND_PID (http://localhost:8000)"
echo -e "✅ Frontend running on PID $FRONTEND_PID (http://localhost:3000)"
echo -e "\n🛑 Press Ctrl+C to stop both servers."

wait $BACKEND_PID $FRONTEND_PID
