#!/usr/bin/env bash
set -euo pipefail

# Simple launcher for the free stack (API + Frontend)
# Requirements:
#  - Python + uvicorn installed (pip install uvicorn[standard])
#  - Node.js + npm installed for the frontend

export NEXT_PUBLIC_API_BASE="http://localhost:8003"

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Free API (port 8003) ..."
(
  cd "$ROOT_DIR/api" && \
  python main.py
) &
API_PID=$!

cleanup() {
  echo "Shutting down..."
  kill "$API_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "Starting Frontend (Free) ..."
(
  cd "$ROOT_DIR/frontend" && \
  npm run dev
)
