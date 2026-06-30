#!/usr/bin/env bash
set -euo pipefail

echo "== JotPop pre-demo check =="

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or not available in PATH."
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is not installed or not available in PATH."
  exit 1
fi

echo "Docker: $(docker --version)"
echo "Compose: $(docker compose version)"

echo "Checking backend health..."
curl -s http://127.0.0.1:8000/health || true
printf "
"

echo "Open http://127.0.0.1:5173 and run Dev > Smoke check."
