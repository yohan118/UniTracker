# UniTracker - platform setup

Docker, nginx, CI and monitoring for the UniTracker app. This is on the `platform`
branch only, the Render deploy still runs from `main`.

## Overview

```
browser -> nginx :80 -> web (gunicorn + flask) :5000 -> sqlite (docker volume)

prometheus :9090  scrapes  web/metrics, node-exporter, cadvisor
grafana    :3000  dashboard "UniTracker" (provisioned)

push -> github actions: tests -> build image -> smoke test -> push to ghcr
                              -> e2e test of the whole stack
cron -> scripts/healthcheck.sh every minute -> ~/unitracker-health.log
```

## Running it

Needs Docker with compose (works in GitHub Codespaces).

```bash
git switch platform
cp .env.example .env     # set a grafana password
docker compose up -d --build
```

- app: http://localhost
- prometheus: http://localhost:9090
- grafana: http://localhost:3000 (admin / password from .env)

`./scripts/e2e-test.sh` starts everything and runs the checks.
`docker compose down` stops it, add `-v` to also delete the data.

## Files

- `Attendance Tracker/Dockerfile` - python 3.12 slim, runs as non-root, gunicorn
- `docker-compose.yml` - web, nginx, prometheus, node-exporter, cadvisor, grafana
- `nginx/default.conf` - reverse proxy to web:5000, /metrics blocked
- `monitoring/` - prometheus config, alert rule, grafana datasource + dashboard
- `scripts/healthcheck.sh`, `scripts/install-cron.sh` - health check + cron job
- `scripts/e2e-test.sh` - end to end test (also used in CI)
- `.github/workflows/ci.yml` - the pipeline
- `Attendance Tracker/tests/` - pytest tests

Changes to the app itself are small: a `/health` route, `/metrics` through
prometheus-flask-exporter, and `DB_PATH` can be set from the environment so the
database can live in the `/data` volume.

## Notes

- gunicorn runs with 1 worker on purpose. Login tokens are stored in memory
  (`active_sessions`), so with more workers people would get logged out randomly.
  Moving sessions to the DB or redis would fix that.
- Only nginx has a public port. The app port and metrics aren't exposed.
- Alert `UniTrackerDown` fires when the app can't be scraped for 1 minute.
- The pipeline builds and pushes the image to GHCR but doesn't deploy it anywhere.
- In Codespaces cron isn't running by default:
  `sudo apt-get install -y cron && sudo service cron start`, then `./scripts/install-cron.sh`.

## TODO

- HTTPS
- deploy the image to a server from the pipeline
- postgres instead of sqlite
- backups for the volume
- alert notifications (email/slack)
