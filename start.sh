#!/bin/bash

# AI Guardian: Global Deployment Initialization Script
echo "AI GUARDIAN | INITIALIZING UNIFIED STACK..."

# 1. Ensure we are in the script directory
cd "$(dirname "$0")"

# 2. Run the Unified Orchestrator
# This starts the Bridge, Flower Server, and Clients with correct port synchronization
python3 run_local.py

# Note: run_local.py handles process management and cleanup on Ctrl+C
