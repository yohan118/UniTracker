import os
import sys
import tempfile

# tests use their own temp database. has to be set before app.py is imported
# because app.py creates the tables at import time
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
