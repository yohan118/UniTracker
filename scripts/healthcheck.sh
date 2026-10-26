#!/bin/bash
# checks /health and logs OK or DOWN. exit code 1 if down
# usage: ./healthcheck.sh [url] [logfile]
URL="${1:-http://localhost/health}"
LOG="${2:-$HOME/unitracker-health.log}"

if curl --silent --fail --max-time 5 "$URL" > /dev/null; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') OK" >> "$LOG"
  exit 0
else
  echo "$(date '+%Y-%m-%d %H:%M:%S') DOWN" >> "$LOG"
  exit 1
fi
