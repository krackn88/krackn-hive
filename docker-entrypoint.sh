#!/bin/sh
set -e
echo "Running migrations..."
alembic upgrade head
echo "Starting API..."
exec uvicorn krackn_hive.main:app --host 0.0.0.0 --port 8000
