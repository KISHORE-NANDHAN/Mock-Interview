from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

auth_bp = Blueprint("auth", __name__)

def get_db():
    conn = sqlite3.connect("database.db", timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


@auth_bp.route("/", methods=["GET", "POST"])
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


@auth_bp.route("/signup", methods=["GET", "POST"])
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


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")
