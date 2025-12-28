import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

@contextmanager
def get_db():
    conn = psycopg2.connect(
        os.getenv("DATABASE_URL"),
        cursor_factory=RealDictCursor,
        options='-c client_encoding=UTF8'
    )
    try:
        yield conn
        conn.commit() # <-- 3. Commit on success
    except Exception:
        conn.rollback() # <-- 4. Rollback on error
        raise
    finally:
        conn.close()
