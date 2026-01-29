from unittest import result
from flask import Blueprint, render_template, request, redirect, session
import sqlite3
import logging
import os
from routes.proctor import stop_proctoring
from routes.proctor import PROCTOR_STATE

logger = logging.getLogger(__name__)
from routes.proctor import start_proctoring
from services.llm_service import generate_questions_llm
from services.evaluation import (
    text_similarity_score,
    evaluate_coding,
    evaluate_technical,
    evaluate_hr
)

exam_bp = Blueprint("exam", __name__)

#------------------------------------------------------------------
import datetime

def dbg(msg, **data):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("debug/exam_debug.log", "a") as f:
        f.write(f"[{timestamp}] [EXAM DEBUG] {msg} | {data}\n")


@exam_bp.route("/set_mode/<mode>")
def set_mode(mode):
    session["exam_mode"] = mode
    return "OK"

@exam_bp.route("/check-violation")
def check_violation():
    if PROCTOR_STATE["violation"]:
        return {"violation": True}
    return {"violation": False}


@exam_bp.route("/stop-proctoring", methods=["POST"])
def stop():
    stop_proctoring()
    return "", 204

#------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect("database.db", timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


@exam_bp.route("/exam/<int:round_id>", methods=["GET", "POST"])
def exam(round_id):

    dbg("EXAM route entered",
        method=request.method,
        round_id=round_id,
        violation=PROCTOR_STATE["violation"]
    )

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


    # FIX: Don't auto-submit here - let the normal POST flow handle it
    # The violation flag will be checked in the POST section
    if PROCTOR_STATE["violation"] and request.method == "GET":
        dbg("Violation detected on GET request, but allowing normal flow")
        # Don't redirect, let the page load normally
        # The frontend will auto-submit via JavaScript

    # ---------------- GET ----------------
    if request.method == "GET":
        session.pop("auto_submit_done", None)
        dbg("EXAM GET started", round_type=round_type)
        mode = session.get("exam_mode", "practice")


        questions = generate_questions_llm(round_type, company)
        if round_type == "technical":
            session["technical_questions"] = [q["question"] for q in questions]
            from flask import current_app
            current_app.config["TECH_QUESTION_CACHE"] = questions

        if round_type == "mcq":
            session["mcq_questions"] = questions

        elif round_type == "reasoning":
            session["reasoning_questions"] = questions
        
        logger.info(
            "Generated questions | round_type=%s | company=%s | questions=%s",
            round_type,
            company,
            questions
        )
        # ---------------- PROCTORING CONTROL ----------------
        from routes.proctor import start_proctoring

        if mode == "strict" and not PROCTOR_STATE["running"]:
            start_proctoring()

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
    dbg(
        "EXAM POST started",
        round_type=round_type,
        violation=PROCTOR_STATE["violation"]
    )
    
    is_forced_submit = PROCTOR_STATE["violation"] or False
    dbg("is_forced_submit resolved", is_forced_submit=is_forced_submit)



    if round_type == "mcq":
        dbg("Evaluating MCQ round")
        questions = session.get("mcq_questions", [])
        
        # FIX: If questions not in session, regenerate them
        if not questions:
            dbg("MCQ questions not found in session, regenerating...")
            questions = generate_questions_llm(round_type, company)
            session["mcq_questions"] = questions
        
        total = len(questions)
        dbg(f"Total MCQ questions: {total}")
        
        for i, q in enumerate(questions):
            submitted = request.form.get(f"q{i}")
            expected = str(q["correct_answer"])
            
            # Debugging the comparison
            dbg(
                f"Question {i+1}",
                submitted=submitted,
                expected=expected,
                match=(str(submitted) == expected)
            )

            if str(submitted) == expected:
                score += 1
            else:
                score += 0
                concepts = ", ".join(q.get("concepts", []))
                concepts = list(set(concepts.split(", ")))
                logger.info("Incorrect answer | question=%s | concepts=%s", q["question"], concepts)

    elif round_type == "reasoning":
        questions = session.get("reasoning_questions", [])
        total = len(questions)

        for i, q in enumerate(questions):
            user_ans = request.form.get(f"q{i}")

            correct = q.get("correct_answer")
            if correct and user_ans == correct:
                score += 1

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


    dbg(
        "Writing score to DB",
        score=score,
        total=total,
        user_id=session.get("user_id"),
        round_id=round_id
    )

    cur.execute("""
    INSERT INTO scores (user_id, company_id, round_id, score, max_score, last_score, avg_score, attempts)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1)

    ON CONFLICT(user_id, round_id)
    DO UPDATE SET
        last_score = score,
        score = excluded.score,
        attempts = attempts + 1,

        avg_score = ROUND(
            ((avg_score * (attempts - 1)) + excluded.score) / attempts,
            2
        ),

        max_score = CASE
            WHEN excluded.score > max_score THEN excluded.score
            ELSE max_score
        END

        """, (session["user_id"], company_id, round_id, score, score, score, score))

    dbg("DB commit successful")


    db.commit()
    db.close()

    session.update({
        "last_score": score,
        "total_questions": total,
        "last_round": round_name,
        "last_company": company
    })
    # ---------------- CLEANUP ----------------
    session.pop("exam_mode", None)
    session.pop("violation", None)

    session["auto_submitted"] = is_forced_submit

    dbg(
        "Session cleaned",
        exam_mode=session.get("exam_mode"),
        violation=PROCTOR_STATE["violation"],
        auto_submitted=session.get("auto_submitted")
    )


    dbg("Redirecting to /score")
    
    # Ensure stop_proctoring doesn't crash the request
    try:
        dbg("Calling stop_proctoring from exam route")
        stop_proctoring()
    except Exception as e:
        logger.error(f"Failed to stop proctoring: {e}")
        dbg(f"Failed to stop proctoring: {e}")
        
    return redirect("/score")
