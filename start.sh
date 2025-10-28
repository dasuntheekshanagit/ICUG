#!/usr/bin/env sh

# Portable launcher that avoids shell parameter expansion in platform UIs
# Ensures numeric workers and sensible defaults in any environment.

PORT="${PORT:-8000}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-2}"

echo "Starting Gunicorn on 0.0.0.0:${PORT} with workers=${WEB_CONCURRENCY}"
exec gunicorn -k uvicorn.workers.UvicornWorker app.main:app \
  --bind 0.0.0.0:"${PORT}" \
  --workers "${WEB_CONCURRENCY}" \
  --timeout 60
