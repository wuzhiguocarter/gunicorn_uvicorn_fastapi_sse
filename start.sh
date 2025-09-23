#!/bin/bash

# Start the ChatBot SSE Server with gunicorn

set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default configuration
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-$(python -c "import multiprocessing; print(multiprocessing.cpu_count() * 2 + 1)")}
LOG_LEVEL=${LOG_LEVEL:-info}

echo "Starting ChatBot SSE Server..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "Workers: $WORKERS"
echo "Log Level: $LOG_LEVEL"

# Start gunicorn
exec gunicorn \
    --bind "$HOST:$PORT" \
    --workers "$WORKERS" \
    --worker-class "uvicorn.workers.UvicornWorker" \
    --worker-tmp-dir "$(python -c 'import tempfile; print(tempfile.gettempdir())')" \
    --log-level "$LOG_LEVEL" \
    --access-logfile "-" \
    --error-logfile "-" \
    --timeout 30 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --graceful-timeout 30 \
    --preload \
    --config gunicorn.conf.py \
    "src.app.main:app"