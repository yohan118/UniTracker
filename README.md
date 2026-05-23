# UniTracker - Attendance Tracking Website
A web app for tracking student attendance. It has separate logins for students, professors, and admins, and shows each course's attendance on a dashboard.

## What it does

- Students, professors, and admins each get their own dashboard
- Sign up is verified with an OTP code before the account works
- Passwords are hashed before being saved
- Courses and attendance percentages are loaded from the database
- Professors and admins can add attendance records; students see their own

## Built with

Python (Flask) on the backend, SQLite for the database, and plain HTML/CSS/JavaScript on the frontend. Deployed on Railway.

## Folders

```
unitrack/
├── railway.toml
├── requirements.txt
├── backend/
│   ├── app.py          # the Flask server and API
│   ├── database.py     # database setup and queries
│   └── otp.py          # makes the OTP codes
└── frontend/
    ├── log_in.html
    ├── student1.html
    ├── professor1.html
    ├── admin1.html
    ├── courses.html
    ├── calander.html
    ├── settings.html
    ├── about.html
    └── contact.html
```

## Running it

```bash
pip install -r requirements.txt
cd backend
python app.py
```

Then open http://127.0.0.1:5000. The database and some demo courses are created on the first run.

## Notes

In this version the OTP code shows up on screen instead of being emailed, so there's nothing to set up to test it.
