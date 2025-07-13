#!/bin/bash

# Capture current directory
PROJECT_DIR="$(pwd)"

# Ports to check and free if in use
PORTS=(8000 5173 9092)

for PORT in "${PORTS[@]}"
do
  if lsof -i :$PORT > /dev/null; then
    echo "Port $PORT is in use. Killing process..."
    PID=$(lsof -ti :$PORT)
    kill -9 $PID
    echo "Process $PID killed."
  else
    echo "Port $PORT is free."
  fi
done

# Start Docker
open -a Docker
sleep 10

echo "Starting Docker containers..."
docker-compose up -d

# Function to open new Terminal tabs with correct working directory
run_tab() {
  osascript <<EOF
tell application "Terminal"
  activate
  do script "cd '$PROJECT_DIR'; conda activate myConda && $1"
end tell
EOF
}

echo "Starting FastAPI backend..."
run_tab "cd backend && uvicorn main:app --reload --port 8000"

echo "Starting Kafka consumer..."
run_tab "cd backend && python3 kafka_consumer_mongo.py"

echo "Starting log simulator..."
run_tab "python3 scripts/log_simulator.py"

echo "Starting React frontend..."
run_tab "cd frontend && npm run dev"

echo "✅ Startup script executed. Check your Terminal tabs."
