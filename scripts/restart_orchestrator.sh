#!/bin/bash
# Restart the AI orchestrator with the latest code.
# Run this after changing LLM settings or updating agent code.
#
# Usage:
#   docker compose exec ai-orchestrator bash /app/scripts/hot_reload.sh
#   OR
#   docker compose up -d --build ai-orchestrator

set -e

echo "=== Restarting AI Orchestrator with latest code ==="
echo ""

# Check if running inside Docker
if [ -f /.dockerenv ]; then
    echo "Running inside container - installing new dependencies..."
    pip install --no-cache-dir langchain-ollama 2>/dev/null || true
    echo "Done. Uvicorn --reload should pick up code changes automatically."
else
    echo "Running outside container - rebuilding..."
    cd "$(dirname "$0")/.."
    docker compose up -d --build ai-orchestrator
    echo ""
    echo "Waiting for orchestrator to be ready..."
    sleep 5
    echo "Done. Check logs with: docker compose logs -f ai-orchestrator"
fi
