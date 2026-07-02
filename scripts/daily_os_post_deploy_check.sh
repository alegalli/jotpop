#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${1:-${BACKEND_URL:-}}"
FRONTEND_URL="${2:-${FRONTEND_URL:-}}"
TEST_EMAIL="${JOTPOP_TEST_EMAIL:-}"
TEST_PASSWORD="${JOTPOP_TEST_PASSWORD:-}"
TIMEZONE="${JOTPOP_TEST_TIMEZONE:-Europe/Dublin}"

if [ -z "$BACKEND_URL" ] || [ -z "$FRONTEND_URL" ]; then
  echo "Usage: ./scripts/daily_os_post_deploy_check.sh https://api.onrender.com https://frontend.vercel.app"
  echo "Optional authenticated checks:"
  echo "  JOTPOP_TEST_EMAIL=you@example.com JOTPOP_TEST_PASSWORD=password123 ./scripts/daily_os_post_deploy_check.sh <backend> <frontend>"
  exit 1
fi

BACKEND_URL="${BACKEND_URL%/}"
FRONTEND_URL="${FRONTEND_URL%/}"

echo "== JotPop Daily OS post-deploy check =="
echo "Backend:  $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo "Timezone: $TIMEZONE"
echo ""

echo "[1/6] Backend health"
HEALTH="$(curl -fsS "$BACKEND_URL/health")"
echo "$HEALTH"
echo "$HEALTH" | grep -q '0.33.0' || echo "Warning: health did not show 0.33.0. Confirm latest deploy finished."
echo ""

echo "[2/6] Frontend reachable"
curl -fsS "$FRONTEND_URL" >/tmp/jotpop_frontend_daily_os.html
if grep -qi "JotPop\|root" /tmp/jotpop_frontend_daily_os.html; then
  echo "Frontend responds."
else
  echo "Frontend responded, but expected marker was not found. Open it manually."
fi
echo ""

echo "[3/6] Public card stats"
curl -fsS "$BACKEND_URL/cards/stats" || echo "Warning: /cards/stats failed; continue manual checks."
echo ""

echo "[4/6] Authenticated Daily OS checks"
if [ -z "$TEST_EMAIL" ] || [ -z "$TEST_PASSWORD" ]; then
  echo "Skipped authenticated checks because JOTPOP_TEST_EMAIL/JOTPOP_TEST_PASSWORD are not set."
  echo "Set them to test /daily-os endpoints automatically."
else
  echo "Registering test user if needed..."
  REGISTER_PAYLOAD="$(python3 - <<PY
import json, os
print(json.dumps({
  'email': os.environ['JOTPOP_TEST_EMAIL'],
  'password': os.environ['JOTPOP_TEST_PASSWORD'],
  'username': os.environ['JOTPOP_TEST_EMAIL'].split('@')[0].replace('+','_').replace('.','_'),
  'display_name': 'JotPop Test'
}))
PY
)"
  curl -sS -o /tmp/jotpop_register.json -w "%{http_code}" \
    -H "Content-Type: application/json" \
    -d "$REGISTER_PAYLOAD" \
    "$BACKEND_URL/auth/register" >/tmp/jotpop_register_code.txt || true
  REG_CODE="$(cat /tmp/jotpop_register_code.txt)"
  if [ "$REG_CODE" = "201" ] || [ "$REG_CODE" = "409" ]; then
    echo "Register/user exists OK ($REG_CODE)."
  else
    echo "Register returned $REG_CODE. Response:"
    cat /tmp/jotpop_register.json
    exit 1
  fi

  echo "Logging in..."
  LOGIN_PAYLOAD="$(python3 - <<PY
import json, os
print(json.dumps({'email': os.environ['JOTPOP_TEST_EMAIL'], 'password': os.environ['JOTPOP_TEST_PASSWORD']}))
PY
)"
  curl -fsS -H "Content-Type: application/json" -d "$LOGIN_PAYLOAD" "$BACKEND_URL/auth/login" >/tmp/jotpop_login.json
  TOKEN="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/jotpop_login.json'))['access_token'])
PY
)"
  AUTH_HEADER="Authorization: Bearer $TOKEN"

  echo "Daily OS status..."
  curl -fsS -H "$AUTH_HEADER" "$BACKEND_URL/daily-os/status?timezone=$TIMEZONE" >/tmp/jotpop_daily_status.json
  python3 - <<'PY'
import json
p=json.load(open('/tmp/jotpop_daily_status.json'))
print('status:', p.get('status'), '| today:', p.get('today'), '| timezone:', p.get('timezone'))
assert p.get('status') == 'ok'
PY

  echo "Do it Today / automatic Minimum Day sync..."
  curl -fsS -H "$AUTH_HEADER" "$BACKEND_URL/daily-os/tasks/today?timezone=$TIMEZONE" >/tmp/jotpop_today.json
  python3 - <<'PY'
import json
p=json.load(open('/tmp/jotpop_today.json'))
print('today:', p.get('today'), '| tasks:', len(p.get('tasks', [])), '| injection:', p.get('auto_injection'))
assert 'tasks' in p
PY

  echo "Minimum Day..."
  curl -fsS -H "$AUTH_HEADER" "$BACKEND_URL/daily-os/minimum-days?timezone=$TIMEZONE" >/tmp/jotpop_minimum.json
  python3 - <<'PY'
import json
p=json.load(open('/tmp/jotpop_minimum.json'))
print('templates:', len(p.get('templates', [])), '| preview:', len(p.get('preview', [])))
assert len(p.get('templates', [])) >= 1
PY

  echo "Plan..."
  curl -fsS -H "$AUTH_HEADER" "$BACKEND_URL/daily-os/plan?timezone=$TIMEZONE" >/tmp/jotpop_plan.json
  python3 - <<'PY'
import json
p=json.load(open('/tmp/jotpop_plan.json'))
print('tomorrow:', len(p.get('tomorrow_tasks', [])), '| next 7:', len(p.get('next_7_days', [])), '| later:', len(p.get('later', [])))
assert 'tomorrow_tasks' in p
PY

  echo "Done..."
  curl -fsS -H "$AUTH_HEADER" "$BACKEND_URL/daily-os/done?timezone=$TIMEZONE" >/tmp/jotpop_done.json
  python3 - <<'PY'
import json
p=json.load(open('/tmp/jotpop_done.json'))
print('last_7_days:', len(p.get('last_7_days', [])), '| totals:', p.get('totals'))
assert len(p.get('last_7_days', [])) == 7
PY

  echo "Daily OS QA..."
  curl -fsS -H "$AUTH_HEADER" "$BACKEND_URL/daily-os/qa?timezone=$TIMEZONE" >/tmp/jotpop_qa.json
  python3 - <<'PY'
import json
p=json.load(open('/tmp/jotpop_qa.json'))
print('qa status:', p.get('status'), '| failures:', p.get('summary', {}).get('failures'))
assert p.get('summary', {}).get('failures', 1) == 0
PY
fi

echo ""
echo "[5/6] CORS/browser reminder"
echo "Open the frontend and run one login/manual check. Automated curl cannot fully validate browser CORS."
echo ""
echo "[6/6] Done"
echo "Daily OS post-deploy check completed."
