# flask-docker-ci

A small Flask app that counts page visits in PostgreSQL. It runs with Docker Compose
(one container for the app, one for the database) and every push is tested and built
by GitHub Actions.

## How it works

```
git push -> GitHub Actions:  test (pytest) -> build image -> smoke test (/health)

browser -> web container (Flask, port 5000) -> db container (PostgreSQL)
                                                      |
                                               volume "dbdata"
                                         (data survives restarts)
```

- `/` adds a visit and shows the total (uses the database)
- `/health` returns `{"status": "ok"}` (no database, so CI can check it)

## Run it

You need Docker with Compose.

```bash
cp .env.example .env      # then change the password in .env
docker compose up -d
curl localhost:5000       # Hello from Docker! Visits so far: 1
curl localhost:5000/health
```

If the first `curl` fails, wait a few seconds, postgres may still be starting.

Stop it with `docker compose down`. The visits are kept in the `dbdata` volume.
`docker compose down -v` also deletes the volume.

## Health check

`health.sh` checks disk space, free memory and that the `web` and `db` containers
are running. The exit code is the number of problems (0 = all good).

```bash
./health.sh
```

To run it every 5 minutes with cron (`crontab -e`), change the path to yours:

```
*/5 * * * * /home/YOUR-USER/flask-docker-ci/health.sh >> /home/YOUR-USER/health.log 2>&1
```

## Tests

```bash
pip install -r requirements.txt
pytest -v
```

Only `/health` is tested because there is no database in GitHub Actions.

## Pipeline

<!-- add a screenshot of a green run here, e.g. docs/pipeline.png -->
![green pipeline](docs/pipeline.png)
