#!/bin/bash
set -e

echo "=== AI Deal Manager - Development Setup ==="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed."; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed."; exit 1; }

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please update .env with your API keys before running the platform."
fi

# Build and start services
echo "Building Docker images..."
docker compose build

echo "Starting infrastructure services..."
docker compose up -d postgres redis minio

echo "Waiting for PostgreSQL to be ready..."
until docker compose exec postgres pg_isready -U dealmanager 2>/dev/null; do
    sleep 1
done

echo "Running Django migrations..."
docker compose run --rm django-api python manage.py migrate

echo "Creating Django superuser..."
docker compose run --rm django-api python manage.py createsuperuser --noinput \
    --username admin --email admin@example.com 2>/dev/null || echo "Superuser already exists."

echo "Starting all services..."
docker compose up -d

echo ""
echo "=== Setup Complete ==="
echo "Frontend:    http://localhost"
echo "API Docs:    http://localhost/api/docs/"
echo "Admin:       http://localhost/admin/"
echo "Langfuse:    http://localhost/langfuse/"
echo "MinIO:       http://localhost:9001 (via docker port mapping if enabled)"
echo ""
