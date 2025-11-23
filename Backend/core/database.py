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
        cursor_factory=RealDictCursor
    )
    try:
        yield conn
    finally:
        conn.close()
