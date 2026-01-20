import sqlite3

def init_db(db_path="database.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ---------------- USERS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        college TEXT,
        branch TEXT,
        year TEXT
    )
    """)

    # ---------------- COMPANIES ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    # ---------------- ROUNDS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rounds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        round_name TEXT,
        round_type TEXT,
        FOREIGN KEY(company_id) REFERENCES companies(id)
    )
    """)

    # ---------------- SCORES ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        company_id INTEGER,
        round_id INTEGER,
        score INTEGER,
        UNIQUE(user_id, round_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(company_id) REFERENCES companies(id),
        FOREIGN KEY(round_id) REFERENCES rounds(id)
    )
    """)

    cur.execute("""
                Alter TABLE scores
                ADD COLUMN max_score real default 0
                """)
    
    cur.execute("""
                Alter TABLE scores
                ADD COLUMN last_score real default 0
                """)
    cur.execute("""
                
    ALTER TABLE scores ADD COLUMN avg_score REAL DEFAULT 0;
    ALTER TABLE scores ADD COLUMN attempts INTEGER DEFAULT 0;
    """)


    # ---------------- DEFAULT DATA ----------------
    companies = {
        "Infosys (SP / DSE)": ["Coding", "Technical Interview", "HR Interview"],
        "Google": ["Coding", "Technical Interview 1", "Technical Interview 2", "Technical Interview 3", "HR Interview"],
        "Microsoft - SDE": ["Coding", "Technical Interview 1", "Technical Interview 2", "HR Interview"],
        "Cognizant": ["Communication", "MCQ", "Coding", "HR Interview"],
        "Deloitte": ["MCQ", "Coding", "HR Interview"],
        "IBM": ["Coding", "Communication", "HR Interview"],
        "Capgemini": ["MCQ", "Coding", "Technical Interview", "HR Interview"],
        "Accenture": ["MCQ", "Coding", "Communication", "HR Interview"],
        "Wipro": ["MCQ", "Technical Interview", "HR Interview"]
    }

    def get_round_type(round_name):
        name = round_name.lower()
        if "mcq" in name:
            return "mcq"
        if "coding" in name:
            return "coding"
        if "communication" in name:
            return "communication"
        if "hr" in name:
            return "hr"
        if "technical" in name:
            return "technical"
        return "mcq"

    for company_name, rounds_list in companies.items():
        cur.execute(
            "INSERT OR IGNORE INTO companies (name) VALUES (?)",
            (company_name,)
        )
        cur.execute(
            "SELECT id FROM companies WHERE name=?",
            (company_name,)
        )
        company_id = cur.fetchone()[0]

        for r in rounds_list:
            cur.execute("""
                INSERT INTO rounds (company_id, round_name, round_type)
                VALUES (?, ?, ?)
            """, (company_id, r, get_round_type(r)))

    conn.commit()
    conn.close()

    print("✅ Database initialized successfully")
