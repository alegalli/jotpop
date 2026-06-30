#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${1:-${BACKEND_URL:-}}"
FRONTEND_URL="${2:-${FRONTEND_URL:-}}"

if [ -z "$BACKEND_URL" ]; then
  echo "Usage: ./scripts/post_deploy_smoke_check.sh https://your-api.onrender.com https://your-frontend.vercel.app"
  echo "Or set BACKEND_URL and FRONTEND_URL env vars."
  exit 1
fi

BACKEND_URL="${BACKEND_URL%/}"
FRONTEND_URL="${FRONTEND_URL%/}"

echo "Checking backend health..."
curl -fsS "$BACKEND_URL/health" | tee /tmp/jotpop_health.json

echo ""
echo "Checking card stats..."
curl -fsS "$BACKEND_URL/cards/stats" | tee /tmp/jotpop_cards.json

echo ""
if [ -n "$FRONTEND_URL" ]; then
  echo "Checking frontend HTML..."
  curl -fsS "$FRONTEND_URL" >/tmp/jotpop_frontend.html
  if grep -qi "JotPop\|root" /tmp/jotpop_frontend.html; then
    echo "Frontend responds."
  else
    echo "Frontend responded, but expected marker was not found. Open it manually."
  fi
fi

echo ""
echo "Post-deploy smoke check completed."
