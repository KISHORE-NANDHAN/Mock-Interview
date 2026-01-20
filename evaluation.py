from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import threading
from dotenv import load_dotenv
load_dotenv()
import os

llm = ChatGroq(
    temperature=0.5,
    groq_api_key= os.getenv("GROQ_API_KEY"),
    model_name= os.getenv("GROQ_MODEL_NAME")
)
def evaluate_long_answer(question, key_points, user_answer):

        # HARD RULE: empty or very short answer → ZERO
        if user_answer is None or len(user_answer.strip()) < 20:
            return 0

        eval_prompt = f"""
        You are a strict examiner.

        Question:
        {question}

        Expected key points:
        {", ".join(key_points)}

        Student answer:
        {user_answer}

        Scoring rules:
        - Completely incorrect or vague → 0-3
        - Partially correct → 4-6
        - Mostly correct → 7-8
        - Fully correct and well explained → 9-10

        Return ONLY a number between 0 and 10.
        """

        chain = ChatPromptTemplate.from_template("{text}") | llm | StrOutputParser()
        score = chain.invoke({"text": eval_prompt})

        # Safe parsing
        digits = "".join(filter(str.isdigit, score))
        if digits == "":
            return 0

        score_int = int(digits[:2])
        return min(score_int, 10)

def evaluate_code(user_code, test_cases):
        result = {
            "passed": False,
            "message": ""
        }

        def safe_exec():
            try:
                safe_globals = {
                    "__builtins__": {
                        "range": range,
                        "len": len,
                        "print": print,
                        "sum": sum,
                        "min": min,
                        "max": max
                    }
                }

                local_env = {}
                exec(user_code, safe_globals, local_env)

                if "solve" not in local_env:
                    result["message"] = (
                        "Missing required function.\n\n"
                        "Define a function named `solve(input_data)` "
                        "that returns the result."
                    )
                    return

                solve = local_env["solve"]

                for tc in test_cases:
                    inp = tc["input"]
                    expected = tc["output"]

                    output = solve(inp[0]) if len(inp) == 1 else solve(*inp)

                    if output != expected:
                        result["message"] = (
                            f"❌ Wrong Output\n"
                            f"Input: {inp}\n"
                            f"Expected: {expected}\n"
                            f"Got: {output}"
                        )
                        return

                result["passed"] = True
                result["message"] = "✅ All test cases passed"

            except Exception as e:
                result["message"] = f"Runtime Error: {e}"

        t = threading.Thread(target=safe_exec)
        t.start()
        t.join(timeout=2)

        if t.is_alive():
            return False, "⏱ Time Limit Exceeded (infinite loop?)"

        return result["passed"], result["message"]