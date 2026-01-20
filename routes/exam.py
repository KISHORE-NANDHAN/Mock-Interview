from unittest import result
from flask import Blueprint, render_template, request, redirect, session
import sqlite3
import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)
from services.llm_service import generate_questions_llm
from services.evaluation import (
    text_similarity_score,
    evaluate_coding,
    evaluate_technical,
    evaluate_hr
)

exam_bp = Blueprint("exam", __name__)

#------------------------------------------------------------------
@exam_bp.route("/set_mode/<mode>")
def set_mode(mode):
    session["exam_mode"] = mode
    return "OK"



#------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect("database.db", timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


@exam_bp.route("/exam/<int:round_id>", methods=["GET", "POST"])
def exam(round_id):
    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT r.round_name, r.round_type, c.name, c.id
        FROM rounds r
        JOIN companies c ON r.company_id = c.id
        WHERE r.id=?
    """, (round_id,))
    round_name, round_type, company, company_id = cur.fetchone()

    # ---------------- GET ----------------
    if request.method == "GET":
        # ---------------- PROCTORING CONTROL ----------------
        mode = session.get("exam_mode", "practice")

        if mode == "strict":
            # Avoid multiple instances
            if not session.get("proctoring_started"):
                subprocess.Popen(
                    [sys.executable, "monitor.py"],
                    stdout=sys.stdout,
                    stderr=sys.stderr
                )

                session["proctoring_started"] = True
                print("🔒 Strict mode: Proctoring started")
        else:
            print("📝 Practice mode: Proctoring OFF")
        # -----------------------------------------------------
        questions = generate_questions_llm(round_type, company)
        if round_type == "technical":
            session["technical_questions"] = [q["question"] for q in questions]
            from flask import current_app
            current_app.config["TECH_QUESTION_CACHE"] = questions
         

        logger.info(
            "Generated questions | round_type=%s | company=%s | questions=%s",
            round_type,
            company,
            questions
        )
        if round_type == "communication":
            return render_template(
                "communication.html",
                company=company,
                round_name=round_name,
                **questions
            )

        return render_template(
            f"{round_type}.html",
            company=company,
            round_name=round_name,
            questions=questions
        )

    # ---------------- POST ----------------
    score = 0
    total = 0

    # ---------------- VIOLATION CHECK ----------------
    if os.path.exists("violation.flag"):
        os.remove("violation.flag")
        session["violation"] = True

        # Stop proctoring state
        session.pop("proctoring_started", None)

        logger.warning("Exam auto-submitted due to violation")
        return redirect("/score")


    if round_type == "mcq":
        questions = session.get("mcq_questions", [])
        total = len(questions)
        for i, q in enumerate(questions):
            if request.form.get(f"q{i}") == q["correct_answer"]:
                score += 1
            else:
                score += 0
                concepts = ", ".join(q.get("concepts", []))
                concepts = list(set(concepts.split(", ")))
                logger.info("Incorrect answer | question=%s | concepts=%s", q["question"], concepts)

    elif round_type == "coding":
        questions = session.get("coding_questions", [])
        total = len(questions) * 10
        for i, q in enumerate(questions):
            result = evaluate_coding(q["question"], request.form.get(f"answer_{i}", ""))
            score += result["score"]

    elif round_type == "communication":
        for i, expected in enumerate(session.get("listening_questions", [])):
            score += text_similarity_score(
                request.form.get(f"listening_{i}", ""), expected
            )
            total += 10

        for i, (_, correct) in enumerate(session.get("fill_questions", [])):
            if request.form.get(f"fill_{i}", "").lower() == correct.lower():
                score += 10
            total += 10

        score += text_similarity_score(
            request.form.get("reading", ""),
            session.get("reading_paragraph", "")
        )
        score += text_similarity_score(
            request.form.get("topic", ""),
            session.get("topic", "")
        )
        total += 20

    elif round_type == "technical":

        qa_pairs = [
            {
                "question": request.form.get(f"question_{i}", ""),
                "answer": request.form.get(f"answer_{i}", "")
            }
            for i in range(len(session.get("technical_questions", [])))
        ]

        logger.info(f"Technical QA Pairs: {qa_pairs}")

        from flask import current_app
        question_bank = current_app.config.get("TECH_QUESTION_CACHE", [])

        from services.technical_evaluator import evaluate_all
        result = evaluate_all(qa_pairs, question_bank)

        score = result["score"]
        total = 100
        session["technical_feedback"] = result.get("improvement_topics", {})



    elif round_type == "hr":
        qa_pairs = [
            {"question": q, "answer": request.form.get(f"answer_{i}", "")}
            for i, q in enumerate(session.get("hr_questions", []))
        ]
        score = evaluate_hr(qa_pairs)["score"]
        total = 100

    cur.execute("""
        INSERT INTO scores (user_id, company_id, round_id, score, max_score, last_score, avg_score, attempts)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)

        ON CONFLICT(user_id, round_id)
        DO UPDATE SET
            last_score = scores.score,
            score = excluded.score,
            attempts = scores.attempts + 1,

            avg_score = ROUND(
                ((scores.avg_score * scores.attempts) + excluded.score) / (scores.attempts + 1),
                2
            ),

            max_score = CASE
                WHEN excluded.score > scores.max_score THEN excluded.score
                ELSE scores.max_score
            END
        """, (session["user_id"], company_id, round_id, score, score, score, score))



    db.commit()
    db.close()

    session.update({
        "last_score": score,
        "total_questions": total,
        "last_round": round_name,
        "last_company": company
    })
    # ---------------- CLEANUP ----------------
    session.pop("proctoring_started", None)

    return redirect("/score")
