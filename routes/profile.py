from flask import Blueprint, render_template, redirect, session
import sqlite3

profile_bp = Blueprint("profile", __name__)

def get_db():
    conn = sqlite3.connect("database.db", timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


@profile_bp.route("/score")
def score_page():
    if "last_score" not in session:
        return redirect("/companies")

    return render_template(
        "score.html",
        score=session["last_score"],
        total=session["total_questions"],
        round_name=session["last_round"],
        company=session["last_company"]
    )


@profile_bp.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE id=?", (session["user_id"],)
    ).fetchone()

    scores = db.execute("""
        SELECT c.name, r.round_name, s.score
        FROM scores s
        JOIN companies c ON s.company_id = c.id
        JOIN rounds r ON s.round_id = r.id
        WHERE s.user_id=?
    """, (session["user_id"],)).fetchall()

    db.close()
    return render_template("profile.html", user=user, scores=scores)
