#!/bin/sh
set -e

if [ -n "$MODEL_DOWNLOAD_URL" ]; then
  echo "Ensuring model is downloaded..."
  python download_assets.py
fi

exec gunicorn app:app \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers 1 \
  --threads 2 \
  --timeout 180 \
  --preload
