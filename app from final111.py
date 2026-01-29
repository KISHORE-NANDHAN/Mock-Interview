from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from prompt import generate_coding_questions, evaluate_coding_answer
from prompt import generate_technical_questions, evaluate_technical_answers
from prompt import generate_hr_questions, evaluate_hr_answers,generate_coding_hint,generate_reasoning_questions
import os
from flask import send_file, abort
from admin import admin_bp

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.secret_key = "exam_secret_key"

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect("database.db", timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

# ---------------- LLM QUESTION GENERATOR ----------------
from prompt import generate_mcq_questions, generate_coding_questions

def generate_questions_llm(round_type, company):
    """
    Fetch questions dynamically from LLM
    """
    round_type = round_type.lower().strip()

    if round_type=='mcq':
        # Call your LLM prompt function for MCQs
        questions = generate_mcq_questions()  # should return a list of dicts
        # Example: [{"question": "...", "options": [...], "answer": "..."}]
        return questions

    elif round_type.startswith("coding"):
        question = generate_coding_questions(company)  # should return dict
        # Example: {"question": "Write a Python function to reverse a string."}
        for q in question:
            q["hint"] = generate_coding_hint(q["question"])
        session["coding_questions"] = question
        return question
    
    elif round_type=='reasoning':
        # Call your LLM prompt function for MCQs
        session.pop("reasoning_questions", None)   
        questions = generate_reasoning_questions()  # should return a list of dicts
        # Example: [{"question": "...", "options": [...], "answer": "..."}]
        return questions

    elif round_type.startswith("communication"):
        # Call your LLM functions for each section
        listening_questions = generate_listening_questions()        # list of questions
        fill_questions = generate_fill_in_blanks()                 # list of tuples (sentence, answer)
        reading_paragraph = generate_reading_paragraph()           # string
        topic = generate_topic()    
        session["listening_questions"] = listening_questions
        session["fill_questions"] = fill_questions
        session["reading_paragraph"] = reading_paragraph
        session["topic"] = topic
                                # string

        # Return all communication questions as a dictionary
        return {
            "listening_questions": listening_questions,
            "fill_questions": fill_questions,
            "reading_paragraph": reading_paragraph,
            "topic": topic
        }
    elif round_type.startswith("technical"):
        questions = generate_technical_questions(company)
        session["technical_questions"] = questions
        return questions
    elif round_type.startswith("hr"):
        questions = generate_hr_questions(company)
        session["hr_questions"] = questions
        return questions


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = request.form
        hashed = generate_password_hash(data["password"])

        db = get_db()
        try:
            db.execute("""
                INSERT INTO users (name,email,password,college,branch,year)
                VALUES (?,?,?,?,?,?)
            """, (
                data["name"], data["email"], hashed,
                data["college"], data["branch"], data["year"]
            ))
            db.commit()
        except Exception as e:
            db.rollback()
            return f"Signup Error: {e}"
        finally:
            db.close()

        return redirect("/")

    return render_template("signup.html")



@app.route("/download_report/<company>/<round_name>")
def download_report(company, round_name):
    filename = f"{company}_{round_name}_report.pdf"
    path = os.path.join("reports", filename)

    if not os.path.exists(path):
        abort(404)

    return send_file(path, as_attachment=True)

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        db.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["name"] = user[1]
            return redirect("/companies")

        return "Invalid credentials"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- COMPANIEProfieS ----------------
@app.route("/companies")
def companies():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    companies = db.execute("SELECT id, name FROM companies").fetchall()
    db.close()

    return render_template("companies.html", companies=companies)
UPLOAD_FOLDER = "uploads"

@app.route("/custom")
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

@app.route("/custom/<filename>")
def start_exam(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)

    with open(path) as f:
        questions = json.load(f)

    session["questions"] = questions
    session["current"] = 0
    session["score"] = 0

    return redirect(url_for("exam_question"))
@app.route("/exam", methods=["GET", "POST"])
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

@app.route("/exam-result")
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

# ---------------- ROUNDS ----------------
@app.route("/rounds/<int:company_id>")
def rounds(company_id):
    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    company = db.execute(
        "SELECT name FROM companies WHERE id=?", (company_id,)
    ).fetchone()[0]

    rounds = db.execute(
        "SELECT id, round_name FROM rounds WHERE company_id=?",
        (company_id,)
    ).fetchall()
    db.close()
    return render_template("rounds.html", company=company, rounds=rounds)

# ---------------- ROUND REDIRECT ----------------
@app.route("/round/<int:round_id>")
def round_page(round_id):
    return redirect(f"/exam/{round_id}")
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from prompt import generate_reading_paragraph, generate_topic, generate_fill_in_blanks, generate_listening_questions
def text_similarity_score(user_text, expected_text):
    if not user_text.strip():
        return 0
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([user_text, expected_text])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    return round(similarity * 10, 2)  # scale 0-10

@app.route("/exam/<int:round_id>", methods=["GET", "POST"])
def exam(round_id):
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT r.round_name, r.round_type, c.name, c.id
        FROM rounds r
        JOIN companies c ON r.company_id = c.id
        WHERE r.id=?
    """, (round_id,))
    round_name, round_type, company, company_id = cur.fetchone()
    print("DEBUG round_type from DB =", repr(round_type))


    # ======================= GET =======================
    if request.method == "GET":
        questions = generate_questions_llm(round_type, company)

        if round_type == "mcq":
            session["mcq_questions"] = questions

        elif round_type == "coding":
            session["coding_questions"] = questions

        elif round_type == "reasoning":
            session["reasoning_questions"] = questions

        elif round_type == "communication":
            session["listening_questions"] = questions["listening_questions"]
            session["fill_questions"] = questions["fill_questions"]
            session["reading_paragraph"] = questions["reading_paragraph"]
            session["topic"] = questions["topic"]

            return render_template(
                "communication.html",
                company=company,
                round_name=round_name,
                listening_questions=questions["listening_questions"],
                fill_questions=questions["fill_questions"],
                reading_paragraph=questions["reading_paragraph"],
                topic=questions["topic"]
            )
        elif round_type.startswith("technical"):
            session["technical_questions"] = questions   # ✅
        
        elif round_type.startswith("hr"):
            session["hr_questions"] = questions
            return render_template(
                "hr.html",
                company=company,
                round_name=round_name,
                questions=questions
            )

        return render_template(
            f"{round_type}.html",
            company=company,
            round_name=round_name,
            questions=questions
        )

    # ======================= POST =======================
    score = 0
    total = 0

    # ======================= MCQ =======================
    if round_type == "mcq":
        questions = session.get("mcq_questions", [])
        total = len(questions)

        for i, q in enumerate(questions):
            user_ans = request.form.get(f"q{i}")
            if user_ans == q["correct_answer"]:
                score += 1

    elif round_type == "reasoning":
        questions = session.get("reasoning_questions", [])
        total = len(questions)

        for i, q in enumerate(questions):
            user_ans = request.form.get(f"q{i}")

            correct = q.get("correct_answer")
            if correct and user_ans == correct:
                score += 1

    # ======================= CODING =======================
    elif round_type == "coding":
        questions = session.get("coding_questions", [])
        total = len(questions) * 10  # each question = 10

        for i, q in enumerate(questions):
            user_code = request.form.get(f"answer_{i}", "")
            evaluation = evaluate_coding_answer(q["question"], user_code)
            score += evaluation["score"]

    # ======================= COMMUNICATION =======================
    elif round_type == "communication":
        # Listening (3 × 10)
        for i, expected in enumerate(session.get("listening_questions", [])):
            user = request.form.get(f"listening_{i}", "")
            score += text_similarity_score(user, expected)
            total += 10

        # Fill in blanks (5 × 10)
        for i, (_, correct) in enumerate(session.get("fill_questions", [])):
            user = request.form.get(f"fill_{i}", "")
            if user.strip().lower() == correct.lower():
                score += 10
            total += 10

        # Reading (10)
        reading = request.form.get("reading", "")
        score += text_similarity_score(reading, session.get("reading_paragraph", ""))
        total += 10

        # Topic (10)
        topic = request.form.get("topic", "")
        score += text_similarity_score(topic, session.get("topic", ""))
        total += 10

    # ======================= TECHNICAL =======================
    elif round_type == "technical":
        questions = session.get("technical_questions", [])
        qa_pairs = []

        for i, q in enumerate(questions):
            qa_pairs.append({
                "question": q,
                "answer": request.form.get(f"answer_{i}", "")
            })

        result = evaluate_technical_answers(qa_pairs)
        score = result["score"]
        total = 100
    
    elif round_type == "hr":
        questions = session.get("hr_questions", [])
        qa_pairs = []

        for i, q in enumerate(questions):
            qa_pairs.append({
                "question": q,
                "answer": request.form.get(f"answer_{i}", "")
            })

        result = evaluate_hr_answers(qa_pairs)
        score = result["score"]
        total = 100


    # ======================= SAVE =======================
    cur.execute("""
        INSERT INTO scores (user_id, company_id, round_id, score)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, round_id)
        DO UPDATE SET score=excluded.score
    """, (session["user_id"], company_id, round_id, score))

    db.commit()
    db.close()

    session["last_score"] = score
    session["total_questions"] = total
    session["last_round"] = round_name
    session["last_company"] = company

    return redirect("/score")

@app.route("/run_code", methods=["POST"])
def run_code():
    data = request.json
    idx = data["question_index"]
    code = data["code"]

    questions = session.get("coding_questions", [])
    question = questions[idx]["question"]

    result = evaluate_coding_answer(question, code)

    return {
        "score": result["score"],
        "feedback": "Test cases evaluated using AI"
    }

@app.route("/score")
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

# ---------------- PROFILE ----------------
@app.route("/profile")
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

@app.route("/coding/<company>", methods=["GET", "POST"])
def coding_round(company):
    round_name = "Coding Round"

    if request.method == "GET":
        questions = generate_coding_questions(skill=company, level="medium")
        session["coding_questions"] = questions
        return render_template(
            "coding.html",
            company=company,
            round_name=round_name,
            questions=questions
        )

    # POST → Evaluate answers
    questions = session.get("coding_questions", [])
    total_score = 0

    for i, q in enumerate(questions):
        user_answer = request.form.get(f"answer_{i}")
        evaluation = evaluate_coding_answer(q["question"], user_answer)

        total_score += evaluation["score"]

    max_score = 30

    return render_template(
        "coding_score.html",
        company=company,
        total_score=total_score,
        max_score=max_score,

    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.register_blueprint(admin_bp)
    app.run(debug=True, use_reloader=False)
