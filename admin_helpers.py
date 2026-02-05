import sqlite3

def get_db():
    return sqlite3.connect("database.db")

def get_filter_options():
    db = get_db()
    colleges = [row[0] for row in db.execute("SELECT DISTINCT college FROM users WHERE college IS NOT NULL AND college != '' ORDER BY college").fetchall()]
    branches = [row[0] for row in db.execute("SELECT DISTINCT branch FROM users WHERE branch IS NOT NULL AND branch != '' ORDER BY branch").fetchall()]
    db.close()
    return colleges, branches
