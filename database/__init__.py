import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "database.db"


def add_column_if_missing(cur, table, column, definition):
    cur.execute(f"PRAGMA table_info({table})")
    existing_cols = {row[1] for row in cur.fetchall()}
    if column not in existing_cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # ---------------- USERS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        college TEXT,
        branch TEXT,
        year TEXT
    )
    """)

    # ---------------- COMPANIES ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    # ---------------- ROUNDS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rounds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        round_name TEXT NOT NULL,
        round_type TEXT NOT NULL,
        UNIQUE(company_id, round_name),
        FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
    )
    """)

    # ---------------- SCORES ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        company_id INTEGER NOT NULL,
        round_id INTEGER NOT NULL,
        score INTEGER DEFAULT 0,
        UNIQUE(user_id, round_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
        FOREIGN KEY(round_id) REFERENCES rounds(id) ON DELETE CASCADE
    )
    """)

    # ---- SAFE COLUMN UPDATES (NO CRASH EVER) ----
    add_column_if_missing(cur, "scores", "max_score", "REAL DEFAULT 0")
    add_column_if_missing(cur, "scores", "last_score", "REAL DEFAULT 0")
    add_column_if_missing(cur, "scores", "avg_score", "REAL DEFAULT 0")
    add_column_if_missing(cur, "scores", "attempts", "INTEGER DEFAULT 0")

    # ---------------- ADMINS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # ---------------- CUSTOM EXAMS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS custom_exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_name TEXT UNIQUE NOT NULL,
        description TEXT,
        difficulty TEXT,
        exam_type TEXT
    )
    """)

    # ---------------- CUSTOM QUESTIONS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS custom_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        options TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        FOREIGN KEY(exam_id) REFERENCES custom_exams(id) ON DELETE CASCADE
    )
    """)

    # ---------------- CUSTOM EXAM SCORES ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS custom_exam_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        exam_name TEXT NOT NULL,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # ---------------- DEFAULT ADMIN ----------------
    cur.execute(
        "INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)",
        ("admin", generate_password_hash("admin123"))
    )

    # ---------------- DEFAULT DATA ----------------
    companies = {
        "Infosys": ["Reasoning", "Coding", "Technical Interview", "HR Interview"],
        "Google": ["Coding", "Technical Interview 1", "Technical Interview 2", "Technical Interview 3", "HR Interview"],
        "Microsoft": ["Coding", "Technical Interview 1", "Technical Interview 2", "HR Interview"],
        "Cognizant": ["Communication", "MCQ", "Coding", "HR Interview"],
        "Deloitte": ["MCQ", "Coding", "HR Interview"],
        "IBM": ["Coding", "Communication", "HR Interview"],
        "Capgemini": ["MCQ", "Coding", "Technical Interview", "HR Interview"],
        "Accenture": ["MCQ", "Coding", "Communication", "HR Interview"],
        "Wipro": ["MCQ", "Technical Interview", "HR Interview"]
    }

    def get_round_type(name):
        name = name.lower()
        if "mcq" in name:
            return "mcq"
        if "coding" in name:
            return "coding"
        if "communication" in name:
            return "communication"
        if "technical" in name:
            return "technical"
        if "hr" in name:
            return "hr"
        if "reasoning" in name:
            return "reasoning"
        return "mcq"

    # ---------------- INSERT COMPANIES & ROUNDS (SAFE) ----------------
    for company_name, rounds in companies.items():
        cur.execute(
            "INSERT OR IGNORE INTO companies (name) VALUES (?)",
            (company_name,)
        )

        cur.execute(
            "SELECT id FROM companies WHERE name = ?",
            (company_name,)
        )
        company_id = cur.fetchone()[0]

        for round_name in rounds:
            cur.execute("""
                INSERT OR IGNORE INTO rounds (company_id, round_name, round_type)
                VALUES (?, ?, ?)
            """, (company_id, round_name, get_round_type(round_name)))

    conn.commit()
    conn.close()
    print("✅ Database initialized safely (idempotent & production-ready)")
