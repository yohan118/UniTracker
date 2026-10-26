#!/bin/bash
# brings up the full stack and tests it end to end. needs a .env file
# also runs in CI (stack job)
set -euo pipefail
cd "$(dirname "$0")/.."

step()  { echo; echo "=== $1"; }
retry() { for _ in $(seq 1 "${TRIES:-40}"); do if "$@"; then return 0; fi; sleep 3; done
          echo "FAILED: $*"; return 1; }
json()  { curl -sf -H "Content-Type: application/json" "$@"; }
PW=$(grep '^GRAFANA_ADMIN_PASSWORD=' .env | cut -d= -f2-)

step "1. start everything"
docker compose up -d --build --wait --wait-timeout 240
docker compose ps

step "2. health check through nginx"
retry curl -sf localhost/health
echo

step "3. /metrics should be 404 from outside"
code=$(curl -s -o /dev/null -w "%{http_code}" localhost/metrics)
echo "HTTP $code"; [ "$code" = "404" ]

step "4. signup + otp + login"
otp=$(json -X POST localhost/api/signup \
  -d '{"name":"CI","email":"ci@example.com","password":"pw123456","role":"student"}' | jq -r .otp)
json -X POST localhost/api/verify-otp -d "{\"email\":\"ci@example.com\",\"code\":\"$otp\"}"
echo
LOGIN='{"email":"ci@example.com","password":"pw123456","role":"student"}'
json -X POST localhost/api/login -d "$LOGIN" | jq -r .message

step "5. data still there after down/up"
docker compose down
docker compose up -d --wait --wait-timeout 240
retry curl -sf localhost/health > /dev/null
json -X POST localhost/api/login -d "$LOGIN" | jq -r .message

step "6. prometheus targets"
targets_up() {
  curl -s localhost:9090/api/v1/targets |
    jq -e '[.data.activeTargets[] | select(.health == "up")] | length == 3' > /dev/null
}
retry targets_up
curl -s localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job): \(.health)"'

step "7. alert rule loaded"
curl -s localhost:9090/api/v1/rules | jq -r '.data.groups[].rules[].name' | grep UniTrackerDown

step "8. grafana datasource + dashboard"
retry curl -sf localhost:3000/api/health > /dev/null
curl -sf -u "admin:$PW" localhost:3000/api/datasources/uid/prometheus/health | jq -r .status
curl -sf -u "admin:$PW" "localhost:3000/api/search?query=UniTracker" | jq -r '.[].title' | grep UniTracker

step "9. healthcheck.sh while up"
./scripts/healthcheck.sh http://localhost/health /tmp/unitracker-health.log && echo "exit code 0"

step "10. stop web, expect errors"
docker compose stop web
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 localhost/ || true)
echo "HTTP $code"; [[ "$code" == 5* ]]
if ./scripts/healthcheck.sh http://localhost/health /tmp/unitracker-health.log; then
  echo "healthcheck.sh should have failed"; exit 1
fi
echo "exit code 1"; tail -2 /tmp/unitracker-health.log

step "11. alert should fire"
firing() {
  curl -s localhost:9090/api/v1/alerts |
    jq -e '.data.alerts[] | select(.labels.alertname == "UniTrackerDown" and .state == "firing")' > /dev/null
}
TRIES=80 retry firing  # can take ~2 min
echo "UniTrackerDown firing"

step "12. start web again"
docker compose start web
retry curl -sf localhost/health
echo; echo "all checks passed"
