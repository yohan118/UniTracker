FROM python:3.12-slim

WORKDIR /app

# deps first so this layer stays cached when only the code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend

# don't run as root
RUN useradd --create-home appuser && mkdir /data && chown appuser /data
USER appuser

ENV DB_PATH=/data/attendance.db
EXPOSE 5000
WORKDIR /app/backend

# 1 worker only: sessions live in memory (active_sessions in app.py)
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "app:app"]
