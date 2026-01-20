from flask import Blueprint, send_file, abort, request, session
import os

from services.evaluation import evaluate_coding

misc_bp = Blueprint("misc", __name__)


@misc_bp.route("/download_report/<company>/<round_name>")
def download_report(company, round_name):
    filename = f"{company}_{round_name}_report.pdf"
    path = os.path.join("reports", filename)

    if not os.path.exists(path):
        abort(404)

    return send_file(path, as_attachment=True)


@misc_bp.route("/run_code", methods=["POST"])
def run_code():
    data = request.json
    idx = data["question_index"]
    code = data["code"]

    questions = session.get("coding_questions", [])
    question = questions[idx]["question"]

    result = evaluate_coding(question, code)

    return {
        "score": result["score"],
        "feedback": "Test cases evaluated using AI"
    }
