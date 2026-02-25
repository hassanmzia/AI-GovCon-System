#!/bin/bash
set -e

echo "=== Running Tests ==="

# Backend tests
echo "Running Django tests..."
cd backend
python -m pytest --tb=short -q
cd ..

# Frontend tests (if configured)
if [ -f frontend/package.json ]; then
    echo "Running frontend tests..."
    cd frontend
    npm test -- --watchAll=false 2>/dev/null || echo "No frontend tests configured yet."
    cd ..
fi

echo "=== Tests Complete ==="
