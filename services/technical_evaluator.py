import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

FILLERS = [
    "basically", "actually", "like", "you know", "in simple words",
    "kind of", "sort of", "i think", "maybe", "probably",
    "something like", "more or less", "at the end of the day",
    "in general", "generally speaking", "as you know",
    "to be honest", "in my opinion", "according to me",
    "it seems", "it looks like", "almost", "just",
    "mainly", "mostly", "simply", "literally",
    "okay", "so", "well", "hmm", "uh", "um"
]


def clean_answer(answer):
    return " ".join(w for w in answer.split() if w.lower() not in FILLERS)


def enhanced_match_score(answer, terms):
    if not terms:
        return 0, []

    answer_emb = model.encode(answer, convert_to_tensor=True)
    matched = 0
    missing = []

    for term in terms:
        if term.lower() in answer.lower():
            matched += 1
        else:
            term_emb = model.encode(term, convert_to_tensor=True)
            if float(util.cos_sim(answer_emb, term_emb)) > 0.55:
                matched += 1
            else:
                missing.append(term)

    return matched / len(terms), missing


def embedding_similarity(answer, correct_answer):
    if not correct_answer.strip():
        return 0

    emb1 = model.encode(answer, convert_to_tensor=True)
    emb2 = model.encode(correct_answer, convert_to_tensor=True)

    return float(util.cos_sim(emb1, emb2))


def depth_score(answer):
    words = len(answer.split())
    if words < 10:
        return 0.3
    elif words < 25:
        return 0.7
    return 1.0


def domain_weight(domain):
    weights = {
        "Programming": 1.0,
        "Problem Solving": 1.0,
        "OOPS": 1.0,
        "DBMS": 1.0,
        "OS": 1.0
    }
    return weights.get(domain, 1.0)


def evaluate_single_answer(answer, qdata):
    answer = clean_answer(answer)

    kt_score, missing_terms = enhanced_match_score(answer, qdata.get("key_terms", []))
    kp_score, missing_points = enhanced_match_score(answer, qdata.get("answer_key_points", []))
    sim_score = embedding_similarity(answer, qdata.get("correct_answer", ""))

    depth = depth_score(answer)

    raw_score = (kt_score * 3) + (kp_score * 4) + (sim_score * 2) + depth

    weighted_score = min(raw_score * domain_weight(qdata.get("domain")), 10)

    return round(weighted_score, 2), missing_terms, missing_points


def evaluate_all(qa_pairs, question_bank):
    total = 0
    evaluated = 0

    weak_topics = {}

    for qa in qa_pairs:
        qdata = next((item for item in question_bank if item["question"] == qa["question"]), None)
        if not qdata:
            continue

        score, missing_terms, missing_points = evaluate_single_answer(qa["answer"], qdata)

        total += score
        evaluated += 1

        # collect weak areas
        if score < 6:
            weak_topics[qdata["question"]] = {
                "missing_key_terms": missing_terms,
                "missing_key_points": missing_points
            }

    if evaluated == 0:
        return {"score": 0, "improvement_topics": {}}

    final_score = round((total / (evaluated * 10)) * 100, 2)

    return {
        "score": final_score,
        "improvement_topics": weak_topics
    }
