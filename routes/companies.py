from flask import Blueprint, render_template, redirect, session
import sqlite3

companies_bp = Blueprint("companies", __name__)

def get_db():
    conn = sqlite3.connect("database.db", timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


@companies_bp.route("/companies")
def companies():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    companies = db.execute("SELECT id, name FROM companies").fetchall()
    db.close()

    return render_template("companies.html", companies=companies)


@companies_bp.route("/rounds/<int:company_id>")
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


@companies_bp.route("/round/<int:round_id>")
def round_page(round_id):
    return redirect(f"/exam/{round_id}")
