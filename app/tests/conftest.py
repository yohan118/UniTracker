import os
import sys
import tempfile

# Use a throw-away database file, so tests never touch real data.
# This must be set BEFORE app.py is imported (app.py creates the tables on import).
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
