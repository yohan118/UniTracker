"""
app.py
------
The actual web server. Flask serves the HTML pages and answers the small
set of API calls the front-end makes (sign up, verify OTP, log in, fetch data).

Design choices, briefly:
  - Passwords are hashed with werkzeug before they ever hit the database.
  - Login hands back a simple token that the browser keeps in localStorage.
    It's not a full JWT setup - just a random string we check against the DB.
    Simple, readable, and good enough for a project like this.
  - Every route returns JSON so the front-end JavaScript can react to it.
"""

import os
import secrets
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

import database
from otp import generate_otp

# The frontend folder sits one level up from here. We point Flask at it so
# visiting "/" actually serves the login page.
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)  # lets the pages talk to the API without browser complaints

# Initialize database on startup - runs whether launched via gunicorn or directly
database.init_db()
database.seed_demo_data()

# Tokens live in memory for simplicity: token -> user id. Restarting the server
# logs everyone out, which is fine for a demo. Swap for a DB table if you want
# them to survive restarts.
active_sessions = {}


# ---------------------------------------------------------------------------
#  Serving the HTML pages
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    # First thing anyone sees is the login / sign-up screen.
    return send_from_directory(FRONTEND_DIR, "log_in.html")


@app.route("/<path:filename>")
def serve_page(filename):
    # Hand back any other html/css/js file the browser asks for by name.
    return send_from_directory(FRONTEND_DIR, filename)


# ---------------------------------------------------------------------------
#  Sign up  ->  send OTP
# ---------------------------------------------------------------------------

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role") or ""

    # Basic sanity checks. The front-end checks too, but never trust the browser.
    if not name or not email or not password or not role:
        return jsonify({"success": False, "message": "Please fill in all fields."}), 400

    conn = database.get_connection()
    cur = conn.cursor()

    # Already registered? Stop here.
    cur.execute("SELECT id, is_verified FROM users WHERE email = ?", (email,))
    existing = cur.fetchone()
    if existing and existing["is_verified"] == 1:
        conn.close()
        return jsonify({"success": False, "message": "An account with this email already exists."}), 409

    # If they signed up before but never verified, we just refresh their row
    # rather than complaining. Less friction.
    hashed = generate_password_hash(password)
    if existing:
        cur.execute(
            "UPDATE users SET name = ?, password = ?, role = ? WHERE email = ?",
            (name, hashed, role, email),
        )
    else:
        cur.execute(
            "INSERT INTO users (name, email, password, role, is_verified) VALUES (?, ?, ?, ?, 0)",
            (name, email, hashed, role),
        )

    # Make a fresh code, wipe any old ones for this email, store the new one.
    code = generate_otp()
    expires = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("DELETE FROM otp_codes WHERE email = ?", (email,))
    cur.execute(
        "INSERT INTO otp_codes (email, code, expires_at) VALUES (?, ?, ?)",
        (email, code, expires),
    )

    conn.commit()
    conn.close()

    # Instead of emailing the code, we hand it straight back to the website,
    # which pops it up on screen for the user to read and type in. Not how a
    # real product would do it, but perfect for a local demo - zero setup.
    return jsonify({
        "success": True,
        "message": "Account created! Here is your verification code:",
        "email": email,
        "otp": code,
    })


# ---------------------------------------------------------------------------
#  Verify the OTP  ->  unlock the account
# ---------------------------------------------------------------------------

@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()

    conn = database.get_connection()
    cur = conn.cursor()

    # Grab the most recent code we issued for this email.
    cur.execute(
        "SELECT code, expires_at FROM otp_codes WHERE email = ? ORDER BY id DESC LIMIT 1",
        (email,),
    )
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "message": "No code found. Please sign up again."}), 404

    # Did they take too long?
    if datetime.now() > datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S"):
        conn.close()
        return jsonify({"success": False, "message": "This code has expired. Request a new one."}), 400

    # Wrong digits?
    if row["code"] != code:
        conn.close()
        return jsonify({"success": False, "message": "Incorrect code. Try again."}), 400

    # All good - flip the account to verified and throw away the used code.
    cur.execute("UPDATE users SET is_verified = 1 WHERE email = ?", (email,))
    cur.execute("DELETE FROM otp_codes WHERE email = ?", (email,))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Account verified! You can log in now."})


# ---------------------------------------------------------------------------
#  Log in
# ---------------------------------------------------------------------------

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role") or ""

    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    conn.close()

    # Walk through the failure cases one at a time so the messages are useful.
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"success": False, "message": "Invalid credentials!"}), 401

    if user["is_verified"] == 0:
        return jsonify({"success": False, "message": "Please verify your email first."}), 403

    if user["role"] != role:
        return jsonify({
            "success": False,
            "message": f"Invalid role. You registered as a {user['role']}.",
        }), 403

    # Success - mint a token and remember who it belongs to.
    token = secrets.token_hex(16)
    active_sessions[token] = user["id"]

    return jsonify({
        "success": True,
        "message": f"Welcome, {user['name']}!",
        "token": token,
        "name": user["name"],
        "role": user["role"],
        "email": user["email"],
    })


# ---------------------------------------------------------------------------
#  Small helper: figure out who's calling from their token
# ---------------------------------------------------------------------------

def current_user_from_token():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = active_sessions.get(token)
    if not user_id:
        return None

    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user


@app.route("/api/me", methods=["GET"])
def me():
    """Lets a page confirm who's logged in (used to greet the user)."""
    user = current_user_from_token()
    if not user:
        return jsonify({"success": False, "message": "Not logged in."}), 401
    return jsonify({
        "success": True,
        "name": user["name"],
        "role": user["role"],
        "email": user["email"],
    })


# ---------------------------------------------------------------------------
#  Courses + attendance (read endpoints for the dashboards)
# ---------------------------------------------------------------------------

@app.route("/api/courses", methods=["GET"])
def get_courses():
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT code, name, instructor, schedule, attendance FROM courses")
    courses = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify({"success": True, "courses": courses})


@app.route("/api/attendance", methods=["GET"])
def get_attendance():
    """Returns the logged-in user's own attendance rows for the records table."""
    user = current_user_from_token()
    if not user:
        return jsonify({"success": False, "message": "Not logged in."}), 401

    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT date, course, status, remarks FROM attendance_records WHERE user_id = ? ORDER BY date DESC",
        (user["id"],),
    )
    records = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify({"success": True, "records": records})


@app.route("/api/attendance", methods=["POST"])
def add_attendance():
    """Lets a professor/admin drop in a new attendance record."""
    user = current_user_from_token()
    if not user:
        return jsonify({"success": False, "message": "Not logged in."}), 401

    data = request.get_json()
    course = data.get("course")
    date = data.get("date")
    status = data.get("status", "present")
    remarks = data.get("remarks", "")
    target_id = data.get("user_id", user["id"])

    if not course or not date:
        return jsonify({"success": False, "message": "Course and date are required."}), 400

    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO attendance_records (user_id, course, date, status, remarks) VALUES (?, ?, ?, ?, ?)",
        (target_id, course, date, status, remarks),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Attendance recorded."})


# ---------------------------------------------------------------------------
#  Admin: list every user
# ---------------------------------------------------------------------------

@app.route("/api/users", methods=["GET"])
def list_users():
    user = current_user_from_token()
    if not user:
        return jsonify({"success": False, "message": "Not logged in."}), 401
    if user["role"] != "admin":
        return jsonify({"success": False, "message": "Admins only."}), 403

    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, email, role, is_verified FROM users ORDER BY id")
    users = []
    for row in cur.fetchall():
        u = dict(row)
        u["status"] = "Active" if u.pop("is_verified") == 1 else "Inactive"
        users.append(u)
    conn.close()
    return jsonify({"success": True, "users": users})


# ---------------------------------------------------------------------------
#  Boot it up
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
