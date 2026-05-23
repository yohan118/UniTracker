# UniTracker
A full-stack web application for managing and visualizing student attendance, with separate dashboards for students, professors, and administrators.

## Features

- **Role-based access** — distinct views and permissions for students, professors, and admins.
- **Secure sign-up flow** — email + OTP verification before an account is activated.
- **Password security** — passwords are hashed (Werkzeug) before they ever reach the database.
- **Live dashboards** — course lists and attendance percentages pulled from the backend in real time.
- **Attendance records** — professors and admins can log attendance; students can view their own history.
- **Calendar view** — attendance visualized by date.

## Tech Stack

- **Backend:** Python, Flask, Flask-CORS
- **Database:** SQLite (standard-library `sqlite3`, no ORM)
- **Frontend:** HTML, CSS, vanilla JavaScript
- **Auth:** token-based sessions, OTP verification, Werkzeug password hashing
- **Deployment:** Railway

## Project Structure

```
unitrack/
├── railway.toml          # Railway deployment config
├── requirements.txt
├── backend/
│   ├── app.py            # Flask server + API routes
│   ├── database.py       # SQLite setup and queries
│   └── otp.py            # OTP code generation
└── frontend/
    ├── log_in.html       # Login / sign-up
    ├── student1.html     # Student dashboard
    ├── professor1.html   # Professor dashboard
    ├── admin1.html       # Admin dashboard
    ├── courses.html      # Course list
    ├── calander.html     # Calendar view
    ├── settings.html
    ├── about.html
    └── contact.html
```

## Running Locally

```bash
pip install -r requirements.txt
cd backend
python app.py
```

Then open `http://127.0.0.1:5000` in your browser. The database and demo course data are created automatically on first run.

## API Overview

| Method | Endpoint            | Purpose                              |
|--------|---------------------|--------------------------------------|
| POST   | `/api/signup`       | Create account and issue an OTP      |
| POST   | `/api/verify-otp`   | Verify the OTP and unlock the account|
| POST   | `/api/login`        | Log in and receive a session token   |
| GET    | `/api/me`           | Get the current logged-in user       |
| GET    | `/api/courses`      | List courses with attendance         |
| GET    | `/api/attendance`   | Get the user's attendance records    |
| POST   | `/api/attendance`   | Add an attendance record             |
| GET    | `/api/users`        | List all users (admin only)          |

## Notes

- For this version, the OTP code is returned to the screen instead of emailed, so the demo runs with zero email setup.
- The SQLite database lives as a file on disk; on a fresh deploy it starts with seeded demo courses.
