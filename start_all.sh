#!/bin/bash

# Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running. Please start Docker Desktop and rerun this script."
  exit 1
fi

# Start Docker containers in detached mode
docker-compose up -d

# Function to open a new terminal tab, activate conda, and run a command
open_tab() {
  local title="$1"
  local command="$2"
  
  osascript <<EOF
tell application "Terminal"
    activate
    tell application "System Events" to keystroke "t" using command down
    delay 0.5
    do script "echo -e '\\033]0;${title}\\007'; source ~/anaconda3/etc/profile.d/conda.sh; conda activate myConda; ${command}" in front window
end tell
EOF
}

# Open tab for FastAPI backend
open_tab "FastAPI Backend" "uvicorn main:app --reload --port 8000"

# Open tab for Kafka consumer
open_tab "Kafka Consumer" "python3 kafka_consumer_mongo.py"

# Open tab for React frontend
open_tab "React Frontend" "cd frontend && npm run dev"

# Open tab for Log Simulator
open_tab "Log Simulator" "python3 scripts/log_simulator.py"

echo "Startup script executed. Check your terminal tabs."
