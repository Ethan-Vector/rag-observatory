#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=./src
export CONFIG_PATH="${CONFIG_PATH:-configs/rag.yaml}"
uvicorn rag_observatory.api:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8090}" --reload
