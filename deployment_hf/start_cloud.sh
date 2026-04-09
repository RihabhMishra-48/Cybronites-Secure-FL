#!/bin/bash

# AI Guardian Cloud Orchestrator
echo "============================================================"
echo "  AI GUARDIAN | STARTING CLOUD INSTANCE"
echo "============================================================"

# Ensure static directory exists (where Dashboard dist was copied)
echo "  [INFO] Static assets found: $(ls static | wc -l) files"

# Start Flower gRPC Server in background
echo "  [1/2] Launching Flower FL Server (Port: $FLOWER_PORT)..."
python -m Cybronites.server.server --flower_port $FLOWER_PORT --rounds $ROUNDS &

# Wait a moment for server initialization
sleep 5

# Start FastAPI Bridge (Foreground)
echo "  [2/2] Launching Guardian Bridge (Port: $PORT)..."
# Bridge will serve static files from /app/static
python -m uvicorn Cybronites.server.bridge:app --host 0.0.0.0 --port $PORT --log-level warning
