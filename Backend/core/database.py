import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from contextlib import contextmanager # <-- 1. IMPORT THIS

load_dotenv()

@contextmanager # <-- 2. ADD THIS DECORATOR
def get_db():
    # Use RealDictCursor so you get back dictionaries
    conn = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit() # <-- 3. Commit on success
    except Exception:
        conn.rollback() # <-- 4. Rollback on error
        raise
    finally:
        conn.close()
