import sqlite3
from flask import current_app

def get_db():
    conn = sqlite3.connect(
        current_app.config.get("DATABASE", "database.db"),
        timeout=10
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row  # optional but recommended
    return conn