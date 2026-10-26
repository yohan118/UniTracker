#!/bin/bash
# adds a cron job that runs healthcheck.sh every minute (only once)
set -e
SCRIPT="$(cd "$(dirname "$0")" && pwd)/healthcheck.sh"
LINE="* * * * * $SCRIPT"

( crontab -l 2>/dev/null | grep -vF "$SCRIPT" ; echo "$LINE" ) | crontab -
crontab -l | grep -F "$SCRIPT"
