#!/bin/bash
# health.sh - quick health report: disk, memory and the docker containers
# exit code = number of problems (0 = all good)
DISK_LIMIT=80
MEM_MIN=200
SERVICES="web db"
problems=0

# go to the project folder so docker compose finds compose.yaml (needed for cron)
cd "$(dirname "$0")" || exit 1

echo "=== Health report: $(hostname) - $(date '+%Y-%m-%d %H:%M') ==="

disk=$(df / --output=pcent | tail -1 | tr -d ' %')
if [ "$disk" -ge "$DISK_LIMIT" ]; then
  echo "DISK:      WARNING - ${disk}% used"
  problems=$((problems + 1))
else
  echo "DISK:      OK - ${disk}% used"
fi

mem=$(free -m | awk '/Mem:/ {print $7}')
if [ "$mem" -lt "$MEM_MIN" ]; then
  echo "MEMORY:    WARNING - only ${mem} MB available"
  problems=$((problems + 1))
else
  echo "MEMORY:    OK - ${mem} MB available"
fi

running=$(docker compose ps --status running --services 2>/dev/null)
for svc in $SERVICES; do
  if echo "$running" | grep -qx "$svc"; then
    echo "CONTAINER: OK - $svc is running"
  else
    echo "CONTAINER: PROBLEM - $svc is not running"
    problems=$((problems + 1))
  fi
done

echo "Problems found: $problems"
exit "$problems"
