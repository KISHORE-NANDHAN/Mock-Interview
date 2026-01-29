from flask import Blueprint, render_template, request, redirect, session
import sqlite3, json
from werkzeug.security import check_password_hash
from matplotlib import pyplot as plt
import os
from flask import render_template, redirect, session, url_for
import pandas as pd
from flask import Blueprint, render_template, request, redirect, session, url_for, send_file


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("database.db")


# ---------------- ADMIN LOGIN ----------------
@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM admins WHERE username=?", (username,))
        admin = cur.fetchone()
        db.close()

        if admin and check_password_hash(admin[2], password):
            session["admin"] = username
            return redirect("/admin/dashboard")

        return "Invalid admin credentials"

    return render_template("admin/login.html")


# ---------------- ADMIN DASHBOARD (HOME) ----------------
@admin_bp.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/admin/login")

    return render_template("admin/dashboard.html")


# ---------------- STUDENTS PAGE ----------------
# ---------------- STUDENTS PAGE ----------------
@admin_bp.route("/students")
def students():
    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db()
    # Fetch only name, college, branch, year
    students = db.execute(
        "SELECT name, college, branch, year FROM users"
    ).fetchall()
    db.close()

    return render_template("admin/students.html", students=students)



# ---------------- RESULTS PAGE ----------------
@admin_bp.route("/results")
def results():
    if "admin" not in session:
        return redirect("/admin/login")

    # Connect to DB and fetch results
    db = get_db()
    results_data = db.execute("""
        SELECT u.name, c.name, r.round_name, s.score
        FROM scores s
        JOIN users u ON s.user_id = u.id
        JOIN companies c ON s.company_id = c.id
        JOIN rounds r ON s.round_id = r.id
    """).fetchall()
    db.close()

    # Convert to pandas DataFrame for plotting
    df = pd.DataFrame(results_data, columns=['Student','Company','Round','Score'])

    # Ensure plots folder exists
    plot_dir = os.path.join("static", "plots")
    os.makedirs(plot_dir, exist_ok=True)

    # --------- 1️⃣ Score Distribution Histogram ---------
    plt.figure(figsize=(6,4))
    plt.hist(df['Score'], bins=range(int(df['Score'].min()), int(df['Score'].max())+2),
             color='#667eea', edgecolor='black')
    plt.title('Score Distribution')
    plt.xlabel('Score')
    plt.ylabel('Number of Students')
    plt.tight_layout()
    score_hist_path = os.path.join(plot_dir, 'score_hist.png')
    plt.savefig(score_hist_path)
    plt.close()

    # --------- 2️⃣ Average Score per Company Bar Chart ---------
    avg_scores = df.groupby('Company')['Score'].mean().reset_index()
    plt.figure(figsize=(6,4))
    plt.bar(avg_scores['Company'], avg_scores['Score'], color='#764ba2')
    plt.title('Average Score per Company')
    plt.ylabel('Average Score')
    plt.xticks(rotation=25, ha='right')
    plt.tight_layout()
    company_scores_path = os.path.join(plot_dir, 'company_scores.png')
    plt.savefig(company_scores_path)
    plt.close()

    # Pass results and plot URLs to template
    return render_template(
        "admin/results.html",
        results=results_data,
        score_hist_url=url_for('static', filename='plots/score_hist.png'),
        company_scores_url=url_for('static', filename='plots/company_scores.png')
    )

# ---------------- CUSTOM EXAM RESULTS PAGE ----------------
@admin_bp.route("/custom-exam-results")
def custom_exam_results():
    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db()
    results = db.execute("""
        SELECT 
            u.name,
            c.exam_name,
            c.score,
            c.total,
            c.attempted_at
        FROM custom_exam_scores c
        JOIN users u ON c.user_id = u.id
        ORDER BY c.attempted_at DESC
    """).fetchall()
    db.close()

    return render_template(
        "admin/custom_exam_results.html",
        results=results
    )


UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

TEMPLATE_JSON = os.path.join(os.getcwd(), "template.json")

# ---------------- EXAMS PAGE ----------------
@admin_bp.route("/exams", methods=["GET", "POST"])
def exams():
    if "admin" not in session:
        return redirect("/admin/login")

    message = ""
    if request.method == "POST":
        exam_name = request.form["exam_name"].strip()
        file = request.files["json_file"]

        if not exam_name or not file:
            message = "Please enter exam name and select a JSON file."
        else:
            try:
                data = json.load(file)

                # Validate JSON format
                for q in data:
                    if not all(k in q for k in ["question", "options", "correct_answer"]):
                        raise ValueError("Invalid JSON format.")
                    if not isinstance(q["options"], dict):
                        raise ValueError("Options must be a dictionary.")

                # Save JSON locally
                filename = f"{exam_name.replace(' ','_')}_custom.json"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                with open(filepath, "w") as f:
                    json.dump(data, f, indent=4)

                message = f"Exam '{exam_name}' submitted successfully!"

            except Exception as e:
                message = f"Error: {str(e)}"

    # Fetch exams from DB
    db = get_db()
    exams_list = db.execute("SELECT * FROM custom_exams").fetchall()
    db.close()

    return render_template("admin/exams.html",
                           exams=exams_list,
                           message=message)


@admin_bp.route("/download_template")
def download_template():
    if os.path.exists(TEMPLATE_JSON):
        return send_file(TEMPLATE_JSON, as_attachment=True)
    else:
        return "Template JSON not found."

# ---------------- LOGOUT ----------------
@admin_bp.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin/login")
