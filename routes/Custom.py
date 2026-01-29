from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

custom_bp = Blueprint("custom", __name__)

UPLOAD_FOLDER = "uploads"

@custom_bp.route("/custom")
def custom_exams():
    exams = []
    for file in os.listdir(UPLOAD_FOLDER):
        if file.endswith("_custom.json"):
            exams.append({
                "name": file.replace("_custom.json", "").replace("_", " ").title(),
                "file": file
            })
    return render_template("custom.html", custom_exams=exams)
import json
from flask import Flask, render_template, request, redirect, url_for, session

@custom_bp.route("/custom/<filename>")
def start_exam(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)

    with open(path) as f:
        questions = json.load(f)

    session["questions"] = questions
    session["current"] = 0
    session["score"] = 0

    return redirect(url_for("exam_question"))
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
            return redirect(url_for("exam_result"))

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
