#!/bin/bash
set -e

# Set default port if not provided
PORT=${PORT:-8001}

# Debug: Print DATABASE_URL status
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  WARNING: DATABASE_URL is not set!"
else
    echo "✅ DATABASE_URL is set (${DATABASE_URL:0:30}...)"
fi

echo "Starting server on port $PORT with Postgres support"

# Start uvicorn
python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT
