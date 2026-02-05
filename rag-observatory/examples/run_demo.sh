#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

ragobs demo
ragobs report --out workspace/report.html
echo "Open workspace/report.html"
