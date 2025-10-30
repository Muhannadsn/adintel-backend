#!/bin/bash
set -e

# Set default port if not provided
PORT=${PORT:-8001}

echo "Starting server on port $PORT with Postgres support"

# Start uvicorn
python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT
