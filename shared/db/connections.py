import os

import psycopg2
from psycopg2.extras import RealDictCursor

from shared.config.config import DB_CONFIG

def get_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', DB_CONFIG["host"]),
        port=os.getenv('DB_PORT', DB_CONFIG["port"]),
        database=os.getenv('DB_NAME', DB_CONFIG["database"]),
        user=os.getenv('DB_USER', DB_CONFIG["user"]),
        password=os.getenv('DB_PASSWORD', DB_CONFIG["password"]),
        cursor_factory=RealDictCursor
    )
    print(conn)
    return conn