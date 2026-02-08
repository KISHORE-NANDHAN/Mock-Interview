from flask import Blueprint, render_template, redirect, session, url_for
import sqlite3

profile_bp = Blueprint("profile", __name__)

# --------------------------------------------------
# Database Helper
# --------------------------------------------------
def get_db():
    conn = sqlite3.connect("database.db", timeout=10)
    conn.row_factory = sqlite3.Row  # dict-style access
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


# --------------------------------------------------
# Score Page (After Completing a Round)
# --------------------------------------------------
@profile_bp.route("/score")
def score_page():
    if "last_score" not in session:
        return redirect(url_for("companies.companies"))

    return render_template(
        "score.html",
        score=session.get("last_score", 0),
        total=session.get("total_questions", 0),
        round_name=session.get("last_round", "Unknown Round"),
        company=session.get("last_company", "Unknown Company")
    )


# --------------------------------------------------
# Profile & Analytics Page
# --------------------------------------------------
@profile_bp.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    # -------- Fetch User --------
    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if not user:
        db.close()
        return redirect(url_for("auth.login"))

    # -------- Fetch Scores (Latest First) --------
    scores = db.execute("""
        SELECT 
            c.name        AS company,
            r.round_name  AS round_name,
            s.score       AS score
        FROM scores s
        JOIN companies c ON s.company_id = c.id
        JOIN rounds r    ON s.round_id   = r.id
        WHERE s.user_id = ?
        ORDER BY s.id DESC
    """, (session["user_id"],)).fetchall()

    # -------- Prepare Chart Data (BACKEND LOGIC) --------
    chart_labels = []
    chart_percentages = []

    for row in scores:
        round_name = row["round_name"].lower()
        score = row["score"]

        if round_name.startswith("mcq"):
            max_marks = 15
        elif "coding" in round_name:
            max_marks = 30
        else:
            max_marks = 100

        chart_labels.append(row["round_name"])
        chart_percentages.append(round((score / max_marks) * 100, 2))

    db.close()

    return render_template(
        "profile.html",
        user=user,
        scores=scores,
        chart_labels=chart_labels,
        chart_percentages=chart_percentages
    )
