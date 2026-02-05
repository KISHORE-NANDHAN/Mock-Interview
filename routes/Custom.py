from flask import Blueprint, render_template, request, redirect, session, url_for
import json
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

custom_bp = Blueprint("custom", __name__)

UPLOAD_FOLDER = "uploads"

@custom_bp.route("/custom")
def custom_exams():
    if "user_id" not in session:
        return redirect("/")

    db = sqlite3.connect("database.db")
    cur = db.cursor()

    # Get user college
    cur.execute("SELECT college FROM users WHERE id=?", (session["user_id"],))
    row = cur.fetchone()
    if not row:
        db.close()
        return "User not found"
    
    user_college = row[0]

    # Filter exams by college and time
    query = """
        SELECT id, exam_name 
        FROM custom_exams 
        WHERE college = ? 
        AND datetime('now', 'localtime') BETWEEN start_time AND end_time
    """
    exams_data = cur.execute(query, (user_college,)).fetchall()
    db.close()

    exams = []
    for eid, name in exams_data:
        exams.append({
            "id": eid,
            "name": name
        })
    return render_template("custom.html", custom_exams=exams)

@custom_bp.route("/custom/exam/<int:exam_id>")
def start_exam(exam_id):
    if "user_id" not in session:
        return redirect("/")

    db = sqlite3.connect("database.db")
    cur = db.cursor()
    
    # 1. Verify access again (college & time)
    cur.execute("SELECT college FROM users WHERE id=?", (session["user_id"],))
    user_row = cur.fetchone()
    if not user_row:
        db.close()
        return redirect("/")
        
    user_college = user_row[0]

    query = """
        SELECT exam_name 
        FROM custom_exams 
        WHERE id = ? 
        AND college = ? 
        AND datetime('now', 'localtime') BETWEEN start_time AND end_time
    """
    exam_row = cur.execute(query, (exam_id, user_college)).fetchone()
    db.close()

    if not exam_row:
        return "Exam not found, expired, or you do not have permission."

    exam_name = exam_row[0]
    filename = f"{exam_name.replace(' ', '_')}_custom.json"
    path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(path):
        return "Exam file not found."

    with open(path) as f:
        questions = json.load(f)

    session["questions"] = questions
    session["current"] = 0
    session["score"] = 0
    session["exam_name"] = exam_name

    return redirect(url_for("custom.exam_question"))
@custom_bp.route("/exam", methods=["GET", "POST"])
def exam_question():
    questions = session.get("questions")
    current = session.get("current", 0)

    if request.method == "POST":
        selected = request.form.get("option")
        correct = questions[current]["correct_answer"]

        if selected == correct:
            session["score"] += 1

        session["current"] += 1
        current += 1

        if current >= len(questions):
            return redirect(url_for("custom.exam_result"))

    return render_template(
        "exam.html",
        question=questions[current],
        index=current + 1,
        total=len(questions)
    )

@custom_bp.route("/exam-result")
def exam_result():
    score = session.get("score", 0)
    total = len(session.get("questions", []))
    exam_name = session.get("exam_name")   # save this when starting exam
    user_id = session.get("user_id")       # from login session

    db = sqlite3.connect("database.db")
    cur = db.cursor()
    cur.execute("""
        INSERT INTO custom_exam_scores (user_id, exam_name, score, total)
        VALUES (?, ?, ?, ?)
    """, (user_id, exam_name, score, total))
    db.commit()
    db.close()

    session.clear()
    return render_template("exam_result.html", score=score, total=total)
