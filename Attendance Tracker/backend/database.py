"""
database.py
-----------
Everything that touches the SQLite file lives here so the rest of the app
doesn't have to worry about SQL details. I kept it plain on purpose - just
sqlite3 from the standard library, no heavy ORM. Easier to read, easier to fix.
"""

import sqlite3
import os

# Put the database file right next to this script so it's easy to find.
DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")


def get_connection():
    # row_factory lets us grab columns by name (row["email"]) instead of by
    # number. Small thing, but it makes the rest of the code much nicer to read.
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the tables the first time we run. Safe to call again - the
    IF NOT EXISTS bit means we won't blow away existing data."""
    conn = get_connection()
    cur = conn.cursor()

    # Users - this is the heart of it. Notice 'is_verified': a freshly signed-up
    # account stays locked until the person types in their OTP code.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL,
            is_verified INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # OTP codes. We store the code, who it's for, and when it dies.
    # Keeping these in their own table means a user can ask for a new code
    # without us tripping over the old one.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT    NOT NULL,
            code       TEXT    NOT NULL,
            expires_at TEXT    NOT NULL,
            created_at TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Courses a student can be attached to. The percentage is stored so the
    # dashboards have something real to show instead of hard-coded numbers.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            code       TEXT    NOT NULL,
            name       TEXT    NOT NULL,
            instructor TEXT,
            schedule   TEXT,
            attendance INTEGER DEFAULT 0
        )
    """)

    # One row per "person showed up (or didn't) to a class on a day".
    # This is what feeds the calendar and the records table.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance_records (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course  TEXT    NOT NULL,
            date    TEXT    NOT NULL,
            status  TEXT    NOT NULL,
            remarks TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


def seed_demo_data():
    """Drop in a few courses and sample attendance rows so the dashboards
    aren't empty on a fresh install. Only runs if the courses table is bare,
    so we don't keep stacking duplicates every restart."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS n FROM courses")
    if cur.fetchone()["n"] == 0:
        demo_courses = [
            ("CS101", "Introduction to Computer Science", "Prof. Smith", "Mon, Wed 10:00 AM", 95),
            ("MATH203", "Calculus II", "Prof. Johnson", "Tue, Thu 1:00 PM", 82),
            ("PHYS101", "Physics for Engineers", "Prof. Williams", "Mon, Wed, Fri 2:00 PM", 75),
            ("ENG202", "Technical Writing", "Prof. Davis", "Fri 9:00 AM", 65),
        ]
        cur.executemany(
            "INSERT INTO courses (code, name, instructor, schedule, attendance) VALUES (?, ?, ?, ?, ?)",
            demo_courses,
        )

    conn.commit()
    conn.close()


# Running this file directly will build a clean database. Handy for testing.
if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print("Database ready at:", DB_PATH)
