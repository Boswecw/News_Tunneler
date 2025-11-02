#!/usr/bin/env bash
# Render start script for News Tunneler backend

set -o errexit  # Exit on error

echo "Running database migrations..."
alembic upgrade head

echo "Starting News Tunneler backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

