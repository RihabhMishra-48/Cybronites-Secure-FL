#!/bin/bash
set -e

# AI Guardian Cloud Orchestrator
echo "============================================================"
echo "  CYBRONITES | CLOUD INSTANCE STARTING"
echo "============================================================"

# Defaults (can be overridden by HuggingFace Secrets)
export FLOWER_PORT=${FLOWER_PORT:-8080}
export PORT=${PORT:-7860}
export ROUNDS=${ROUNDS:-5}
export PYTHONPATH=/app

# Verify static assets exist
echo "  [INFO] Static dashboard assets: $(ls /app/static 2>/dev/null | wc -l) files"

# Verify DB can initialize (bridge startup calls init_db on import)
echo "  [INFO] Verifying database initialization..."
python -c "from Cybronites.server.db import init_db; init_db(); print('  [DB] guardian.db ready.')"

# Start Flower gRPC Server in background
echo "  [1/2] Launching Flower FL Server (Port: $FLOWER_PORT)..."
python -m Cybronites.server.server --flower_port $FLOWER_PORT --rounds $ROUNDS &

# Wait for Flower to initialize before bridge starts
sleep 5

# Start FastAPI Bridge (Foreground — serves dashboard + API + WebSocket)
echo "  [2/2] Launching Guardian Bridge (Port: $PORT)..."
exec python -m uvicorn Cybronites.server.bridge:app \
    --host 0.0.0.0 \
    --port $PORT \
    --log-level warning
