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
            r.round_type  AS round_type, 
            s.score       AS score
        FROM scores s
        JOIN companies c ON s.company_id = c.id
        JOIN rounds r    ON s.round_id   = r.id
        WHERE s.user_id = ?
        ORDER BY s.id DESC
    """, (session["user_id"],)).fetchall()

    # -------- Prepare Chart Data (AGGREGATED) --------
    # User Request: Average scores per round type across all companies
    
    aggregation = {}
    
    for row in scores:
        # Use round_type for grouping (fallback to round_name if type is missing)
        r_type = row["round_type"] if row["round_type"] else row["round_name"]
        r_type = r_type.title() # "Mcq" -> "Mcq" (or capitalize properly)
        
        # Normalize specific names if needed
        if r_type.lower() == "mcq": r_type = "MCQ"
        if r_type.lower() == "hr": r_type = "HR"
        
        score = row["score"]
        
        # Determine max marks based on type (Logic from previous code)
        # Note: Ideally this should be in the DB, but keeping existing logic for consistency
        low_type = r_type.lower()
        if "mcq" in low_type:
            max_marks = 15
        elif "coding" in low_type:
            max_marks = 30
        else:
            max_marks = 100
            
        percent = (score / max_marks) * 100
        
        if r_type not in aggregation:
            aggregation[r_type] = {"total_percent": 0, "count": 0}
            
        aggregation[r_type]["total_percent"] += percent
        aggregation[r_type]["count"] += 1

    # Convert to lists for Chart.js
    chart_labels = []
    chart_percentages = []
    
    # Sort for consistent display order? Alphabetical is fine.
    for r_type in sorted(aggregation.keys()):
        data = aggregation[r_type]
        avg = data["total_percent"] / data["count"]
        chart_labels.append(r_type)
        chart_percentages.append(round(avg, 2))

    db.close()

    return render_template(
        "profile.html",
        user=user,
        scores=scores,
        chart_labels=chart_labels,
        chart_percentages=chart_percentages
    )
