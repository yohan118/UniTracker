import os

import psycopg2
from flask import Flask

app = Flask(__name__)


def get_db():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user="postgres",
        password=os.environ.get("DB_PASSWORD", ""),
        dbname="postgres",
    )


@app.route("/")
def home():
    conn = get_db()
    with conn, conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS visits (id SERIAL PRIMARY KEY)")
        cur.execute("INSERT INTO visits DEFAULT VALUES")
        cur.execute("SELECT COUNT(*) FROM visits")
        count = cur.fetchone()[0]
    conn.close()
    return f"Hello from Docker! Visits so far: {count}\n"


@app.route("/health")
def health():
    # no database call here on purpose, so CI can check it without postgres
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
