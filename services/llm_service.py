from flask import session

from pmt import (
    generate_mcq_questions,
    generate_coding_questions,
    generate_coding_hint,
    generate_technical_questions,
    generate_hr_questions,
    generate_reading_paragraph,
    generate_topic,
    generate_fill_in_blanks,
    generate_listening_questions
)


def generate_questions_llm(round_type: str, company: str):
    """
    Generate questions dynamically based on round type.
    Pure business logic – no rendering, no DB.
    """
    round_type = round_type.lower().strip()

    # ---------------- MCQ ----------------
    if round_type == "mcq":
        return generate_mcq_questions()

    # ---------------- CODING ----------------
    if round_type.startswith("coding"):
        questions = generate_coding_questions(company)

        for q in questions:
            q["hint"] = generate_coding_hint(q["question"])

        session["coding_questions"] = questions
        return questions

    # ---------------- COMMUNICATION ----------------
    if round_type.startswith("communication"):
        listening_questions = generate_listening_questions()
        fill_questions = generate_fill_in_blanks()
        reading_paragraph = generate_reading_paragraph()
        topic = generate_topic()

        session["listening_questions"] = listening_questions
        session["fill_questions"] = fill_questions
        session["reading_paragraph"] = reading_paragraph
        session["topic"] = topic

        return {
            "listening_questions": listening_questions,
            "fill_questions": fill_questions,
            "reading_paragraph": reading_paragraph,
            "topic": topic
        }

    # ---------------- TECHNICAL ----------------
    if round_type.startswith("technical"):
        questions = generate_technical_questions(company)
        session["technical_questions"] = questions
        return questions

    # ---------------- HR ----------------
    if round_type.startswith("hr"):
        questions = generate_hr_questions(company)
        session["hr_questions"] = questions
        return questions

    return []
