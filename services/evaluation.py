from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from pmt import (
    evaluate_coding_answer,
    evaluate_technical_answers,
    evaluate_hr_answers
)


def text_similarity_score(user_text: str, expected_text: str) -> float:
    """
    Returns similarity score between 0–10
    """
    if not user_text.strip():
        return 0.0

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([user_text, expected_text])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

    return round(similarity * 10, 2)


# ---------------- CODING ----------------
def evaluate_coding(question: str, user_code: str) -> dict:
    return evaluate_coding_answer(question, user_code)


# ---------------- TECHNICAL ----------------
def evaluate_technical(qa_pairs: list) -> dict:
    return evaluate_technical_answers(qa_pairs)


# ---------------- HR ----------------
def evaluate_hr(qa_pairs: list) -> dict:
    return evaluate_hr_answers(qa_pairs)
