from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re
from dotenv import load_dotenv
load_dotenv()
import os

llm = ChatGroq(
    temperature=0.5,
    groq_api_key= os.getenv("GROQ_API_KEY"),
    model_name= os.getenv("GROQ_MODEL_NAME") 
)
def generate_mcq_questions(subject_name='multiple programming, sql, aptitude and all', num_mcq=15, difficulty_level='medium'):
    prompt_template = """
    You are an expert question paper setter.

    Generate {num_mcq} multiple-choice questions for the subject below.
    Give 15 questions only.

    Subject: {subject_name}
    Difficulty Level: {difficulty_level}

    STRICTLY return output in this JSON format ONLY:

    [
      {{
        "question": "Question text",
        "options": {{
          "a": "Option A",
          "b": "Option B",
          "c": "Option C",
          "d": "Option D"
        }},
        "correct_answer": "a",
        "concept": ["concept1", "concept2"]
      }}
    ]

    Rules:
    - Do NOT add explanations
    - Do NOT add extra text
    - Ensure correct_answer is one of a/b/c/d
    """

    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm | StrOutputParser()

    response = chain.invoke({
        "subject_name": subject_name,
        "difficulty_level": difficulty_level,
        "num_mcq": num_mcq,
    })

    return json.loads(response)

def generate_long_questions(subject_name, num_questions, difficulty_level):
        prompt_template = """
        You are an expert examiner.

        Generate {num_questions} long answer questions.

        Subject: {subject_name}
        Difficulty Level: {difficulty_level}

        STRICTLY return output in JSON format ONLY:

        [
          {{
            "question": "Explain question text",
            "key_points": ["point1", "point2", "point3"]
          }}
        ]
        """

        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | llm | StrOutputParser()

        import json
        response = chain.invoke({
            "subject_name": subject_name,
            "difficulty_level": difficulty_level,
            "num_questions": num_questions
        })

        return json.loads(response)

def generate_coding_questions(skill='general', level='hard'):
        prompt = f"""
        You are a coding examiner.

        Generate EXACTLY 3 Python coding questions.

        Skill: {skill}
        Difficulty: {level}

        Return ONLY valid JSON.
        Do NOT include markdown or explanation.

        JSON FORMAT:

        [
          {{
            "question": "Problem statement",
            "test_cases": [
              {{ "input": [[10, 20, 30]], "output": 60 }},
              {{ "input": [[5, 5]], "output": 10 }}
            ]
          }}
        ]
        """

        chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
        raw = chain.invoke({"text": prompt})

        try:
            json_text = re.search(r"\[.*\]", raw, re.DOTALL).group()
            return json.loads(json_text)
        except:
            return []
        
def generate_reasoning_questions():
        import json, re  # ✅ FIX 1

        prompt = """
        Generate EXACTLY 15 reasoning MCQ questions.

        Topics:
        - Number Series
        - Coding-Decoding
        - Blood Relations
        - Direction Sense
        - Analogy
        - Odd One Out

        Difficulty: Medium

        STRICT RULES:
        - Return ONLY valid JSON
        - No markdown
        - No explanation

        JSON FORMAT:
        [
          {
            "question": "Question text",
            "options": {
              "a": "option",
              "b": "option",
              "c": "option",
              "d": "option"
            },
            "answer": "a"
          }
        ]
        """

        chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
        raw = chain.invoke({"text": prompt})

        try:
            json_text = re.search(r"\[.*\]", raw, re.DOTALL).group()
            questions = json.loads(json_text)

            if len(questions) != 15:
                raise ValueError("Not 15 questions")

            return questions

        except Exception as e:
            return e
        

def generate_listening_questions():
    prompt = f"""
    Generate 3 short sentences for listening and speaking practice on the topic of communication skills.
    Directly give the sentences without any introduction.
    Return only the sentences, no explanations.
    """
    chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
    response = chain.invoke({"text": prompt})
    sentences = [line.strip() for line in response.split("\n") if line.strip()]
    return sentences[:3]

def generate_fill_in_blanks():
        prompt = """
        Generate EXACTLY 5 fill-in-the-blank questions for communication skills.
        Directly give the questions without any introduction.

        RULES:
        - Use ___ for the blank
        - Return ONLY plain text
        - One question per line
        - Format: Sentence with ___ , Answer

        Example:
        Communication improves ___ skills., speaking
        """

        chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
        response = chain.invoke({"text": prompt})

        blanks = []
        for line in response.split("\n"):
            if "," in line and "___" in line:
                sentence, answer = line.rsplit(",", 1)
                blanks.append((sentence.strip(), answer.strip()))

        # Safety fallback
        while len(blanks) < 5:
            blanks.append(("Communication builds ___ confidence.", "self"))

        return blanks[:5]

def generate_reading_paragraph():
    prompt = """
    Generate a short paragraph (3-4 sentences) on the topic of communication skills.
    Directly give the paragraph without any introduction.
    The paragraph should be easy to read aloud.
    Return ONLY the paragraph text.
    """
    chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
    response = chain.invoke({"text": prompt})
    return response.strip()

def generate_topic():
    prompt = """
    Suggest a topic for a short speaking exercise on communication skills.
    directly give the topic without any introduction.
    Return ONLY the topic text.
    """
    chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
    response = chain.invoke({"text": prompt})
    return response.strip()

def evaluate_coding_answer(question, user_code):
    prompt = f"""
    You are a strict coding evaluator.

    Question:
    {question}

    User Code:
    {user_code}

    Score out of 10.
    Return ONLY JSON.

    {{
      "score": 0-10
    }}
    """

    chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
    raw = chain.invoke({"text": prompt})

    try:
        return json.loads(re.search(r"\{.*\}", raw, re.DOTALL).group())
    except:
        return {"score": 0}


def generate_technical_questions(company="general"):
    json_format = """
    [
      {
        "question": "Question text here",
        "domain": "One of: Programming, DBMS, OOPS, OS, Problem Solving",
        "key_terms": ["term1", "term2", "term3"],
        "answer_key_points": ["point1", "point2", "point3"],
        "correct_answer": "Detailed answer text here"
      }
    ]
    """

    prompt = (
        f"You are a senior technical interviewer.\n\n"
        f"Generate EXACTLY 10 theoretical technical interview questions "
        f"for a candidate applying to {company}.\n\n"
        "Questions must cover these domains:\n"
        "- Programming (Java/Python/C/SQL)\n"
        "- DBMS\n"
        "- OOPS\n"
        "- Operating Systems\n"
        "- Information Security\n"
        "- HTML/CSS/JavaScript\n\n"
        "Each question must also include key technical terms expected in the answer.\n\n"
        "RULES:\n"
        "- Return ONLY JSON\n"
        "- No explanations\n"
        "- No numbering\n"
        "- Do not add anything outside the JSON\n"
        "- No coding questions, only theoretical questions\n\n"
        "JSON FORMAT:\n"
        + json_format
    )

    chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
    raw = chain.invoke({"text": prompt})

    try:
        return json.loads(re.search(r"\[.*\]", raw, re.DOTALL).group())
    except Exception as e:
        print("Error parsing questions:", e)
        return []

def evaluate_technical_answers(qa_pairs):
    prompt = f"""
    You are a strict technical interviewer.

    Evaluate the following interview questions and answers.
    Give a total score out of 100 for 10 questions
    each question carries 10 marks,

    Questions and Answers:
    {json.dumps(qa_pairs, indent=2)}

    RULES:
    - Consider correctness, clarity, depth
    - Return ONLY JSON
    - For each question 10 score only if this perfect match
      if perfect match only give score.

    JSON FORMAT:
    {{
      "score": 0-100
    }}
    """

    chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
    raw = chain.invoke({"text": prompt})

    try:
        return json.loads(re.search(r"\{.*\}", raw, re.DOTALL).group())
    except:
        return {"score": 0}
    

def generate_hr_questions(company="general"):
    prompt = f"""
    You are a senior HR interviewer.

    Generate EXACTLY 5 HR interview questions
    for a candidate applying to {company}.

    Questions should assess:
    - Motivation
    - Communication skills
    - Attitude
    - Teamwork
    - Career goals

    RULES:
    - Return ONLY JSON
    - No explanation
    - No numbering
    - Questions must be open-ended

    JSON FORMAT:
    [
      "Question 1",
      "Question 2"
    ]
    """

    chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
    raw = chain.invoke({"text": prompt})

    try:
        return json.loads(re.search(r"\[.*\]", raw, re.DOTALL).group())
    except:
        return []


def evaluate_hr_answers(qa_pairs):
    prompt = f"""
    You are a professional HR interviewer.

    Evaluate the following HR interview questions and answers.
    Give a total score out of 100 for 5 questions.
    Each question carries 20 marks.

    Questions and Answers:
    {json.dumps(qa_pairs, indent=2)}

    EVALUATION CRITERIA:
    - Relevance to question
    - Clarity of expression
    - Confidence
    - Honesty
    - Professional attitude

    RULES:
    - Be strict
    - If answer is vague or very short, give low marks
    - Full 20 marks ONLY for excellent answers
    - Return ONLY JSON
    - No explanation

    JSON FORMAT:
    {{
      "score": 0-100
    }}
    """

    chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
    raw = chain.invoke({"text": prompt})

    try:
        return json.loads(re.search(r"\{.*\}", raw, re.DOTALL).group())
    except:
        return {"score": 0}

def generate_coding_hint(question):
    prompt = f"""
    You are an AI coding mentor.

    Given the following coding problem, generate a SHORT and HELPFUL hint
    WITHOUT giving the full solution.

    Problem:
    {question}

    RULES:
    - Do NOT give code
    - Do NOT give full logic
    - Explain approach in 2–3 lines
    - Focus on thinking strategy only
    - Return ONLY plain text
    """

    chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
    response = chain.invoke({"text": prompt})

    return response.strip()
