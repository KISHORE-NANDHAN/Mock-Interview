import streamlit as st
from pmt import generate_mcq_questions, generate_long_questions, generate_coding_questions, generate_reasoning_questions, generate_fill_in_blanks, generate_reading_paragraph, generate_topic, generate_listening_questions
from evaluation import evaluate_long_answer, evaluate_code
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import queue
# ----------------- Session Initialization -----------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# ----------------- HOME PAGE -----------------
def home_page():
    st.markdown(
        """
        <style>
        .center-title {
            text-align: center;
            font-size: 50px;
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: bold;
            color: #4B0082;
            margin-bottom: 16px;
        }
        .input-container {
            background-color: #F0F8FF;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            max-width: 600px;
            margin: auto;
        }
        .start-btn {
            background-color: #4B0082;
            color: white;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 10px;
        }
        </style>
        """, unsafe_allow_html=True
    )
    with st.container():
        st.markdown('<div class="center-title">AI-POWERED INTERVIEW ASSESSMENT</div>', unsafe_allow_html=True)
        
        # Input fields container
        with st.container(border=True):
            st.markdown(" ")
            st.markdown(" ")
            col1,col2,col3=st.columns([1,1,1])         
            skill = col1.text_input("Enter Skill", placeholder="e.g., Data Science")
            level = col2.selectbox("Select Exam Level", ["Easy", "Medium", "Hard"])
            exam_type = col3.selectbox(
                "Select Exam Type",
                ["MCQ", "Long Answers", "Coding", "Reasoning", "Communication"]
            )
            col1,col2,col3=st.columns([1.4,1,1])
            # Start button
            if col2.button("Start Exam",type="primary"):
                if skill.strip() == "" and exam_type != "Communication":
                    st.warning("⚠️ Please enter a skill")
                    return
                else:
                    st.success(f"✅ Exam started for skill: {skill}, Level: {level}, Type: {exam_type}")            
                st.session_state.skill = skill
                st.session_state.level = level
                st.session_state.exam_type = exam_type
                st.session_state.page = exam_type.lower().replace(" ", "_")
                st.rerun()
            st.markdown(" ")
            st.markdown(" ")

# ----------------- COMMON EXAM PAGE -----------------
def exam_page(title, description):
    st.title(title)

    st.info(f"""
    **Skill:** {st.session_state.skill}  
    **Level:** {st.session_state.level}  
    **Exam Type:** {st.session_state.exam_type}
    """)

    st.write(description)

    if st.button("⬅ Back to Home"):
        st.session_state.page = "home"
        st.rerun()

# ---------------- INIT SESSION STATE ----------------
defaults = {
    "exam_running": False,
    "violation_detected": False,
    "auto_submitted": False,
    "submitted": False,
    "mcqs": [],
    "user_answers": {}
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------- PAGE ROUTER -----------------
if st.session_state.page == "home":
    home_page()

elif st.session_state.page == "long_answers":
    st.markdown(
        """
        <style>
        .center-title {
            text-align: center;
            font-size: 30px;
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: bold;
            color: #4B0082;
            margin-bottom: 16px;
        }
        </style>
        """, unsafe_allow_html=True
    )
    with st.container(border=True):
        col1,col2=st.columns([12,1])
        col1.markdown(f'<div class="center-title">📝 {st.session_state.skill.upper()} - Long Answer Exam</div>', unsafe_allow_html=True)
        if col2.button("🏠"):
            st.session_state.page = "home"
            del st.session_state.long_questions
            del st.session_state.long_answers
            del st.session_state.long_scores
            st.rerun()

        # ---------------- SESSION INIT ----------------
        if "long_questions" not in st.session_state:
            st.session_state.long_questions = []
            st.session_state.long_answers = {}
            st.session_state.long_scores = {}
            st.session_state.long_submitted = False
            st.session_state.long_total_score = 0
        col1,col2,col3=st.columns([1.4,1,1])
        if col2.button("Generate Exam",type="primary"):
            #draw line
            st.markdown("---")
            with st.spinner("Generating questions..."):
                st.session_state.long_questions = generate_long_questions(
                    subject_name=st.session_state.skill,
                    num_questions=5,
                    difficulty_level=st.session_state.level
                )
                st.session_state.long_answers = {}
                st.session_state.long_scores = {}
                st.session_state.long_submitted = False
                st.session_state.long_total_score = 0

        # ---------------- DISPLAY QUESTIONS ----------------
        if st.session_state.long_questions:
            for idx, q in enumerate(st.session_state.long_questions):
                st.subheader(f"Q{idx + 1}. {q['question']}")
                answer = st.text_area(
                    "Enter your answer:",
                    height=160,
                    key=f"long_ans_{idx}"
                )

                st.session_state.long_answers[idx] = answer
            col1,col2,col3=st.columns([1.4,1,1])
            button = col2.button("Submit Exam",type="primary")
            #with st.sidebar:
            #    monitor_students()
            # ---------------- SUBMIT ----------------
            if button:
                total_score = 0
                with st.spinner("Evaluating answers..."):
                    for idx, q in enumerate(st.session_state.long_questions):
                        user_ans = st.session_state.long_answers.get(idx, "")

                        if user_ans.strip() == "":
                            score = 0
                        else:
                            score = evaluate_long_answer(
                                q["question"],
                                q["key_points"],
                                user_ans
                            )

                        st.session_state.long_scores[idx] = score
                        total_score += score

                st.session_state.long_total_score = total_score
                st.session_state.long_submitted = True

        # ---------------- RESULT ----------------
        if st.session_state.long_submitted:
            st.success("✅ Exam Completed!")
            col1,col2=st.columns([1,1])
            # Question-wise scores
            for idx in range(len(st.session_state.long_questions)):
                col1.write(f"**Question {idx + 1} Score:** {st.session_state.long_scores[idx]} / 10")

            max_total = len(st.session_state.long_questions) * 10
            #make final score colorful
            col1.markdown(f"""
            <style> 
            .final-score {{
                font-size: 24px;
                font-weight: bold;
                color: #4B0082;
            }}
            </style>
            """, unsafe_allow_html=True)
            col1.markdown(f'<div class="final-score">Final Score: {st.session_state.long_total_score} / {max_total}</div>', unsafe_allow_html=True)
            #draw donut chart score in streamlit
            import plotly.express as px
            fig = px.pie(
                names=["Score", "Remaining"],
                values=[st.session_state.long_total_score, max_total - st.session_state.long_total_score],
                hole=0.6,
                color_discrete_sequence=["#DFD8D8", "#09823E"]
            )
            fig.update_traces(textinfo='none')
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=250)
            col2.plotly_chart(fig, use_container_width=True)

            percentage = (st.session_state.long_total_score / max_total) * 100

            if percentage >= 80:
                st.info("Excellent understanding and explanation skills. 🎯")
            elif percentage >= 50:
                st.info("Good attempt, but answers need more depth. 👍")
            else:
                st.info("Needs improvement. Please revise the concepts. 📘")

        # ---------------- BACK ----------------



# ---------------- MCQ PAGE ----------------
elif st.session_state.page == "mcq":

    with st.container(border=True):
        st.markdown(
        """
        <style>
        .center-title {

            text-align: center;
            font-size: 30px;
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: bold;
            color: #4B0082;
            margin-bottom: 16px;
        }
        </style>
        """, unsafe_allow_html=True
    )
        col1,col2=st.columns([12,1])
        col1.markdown(f'<div class="center-title">📝 {st.session_state.skill.upper()} - MCQ Exam</div>', unsafe_allow_html=True)
        if col2.button("🏠"):
            st.session_state.exam_running = False
            st.session_state.page = "home"
            del st.session_state.mcqs
            del st.session_state.user_answers
            del st.session_state.score
            del st.session_state.total
            del st.session_state.submitted
            st.rerun()
            # Clear MCQ session data
            
        col1,col2,col3=st.columns([1,1,1])
        # ---------------- GENERATE EXAM ----------------
        if col2.button("Generate MCQ Exam",type="primary"):
            with st.spinner("Generating questions..."):
                st.session_state.mcqs = generate_mcq_questions(
                    subject_name=st.session_state.skill,
                    num_mcq=10,
                    difficulty_level=st.session_state.level
                )
                st.session_state.user_answers = {}
                st.session_state.exam_running = True
                st.session_state.submitted = False
                st.session_state.violation_detected = False
                st.session_state.auto_submitted = False

        #draw line
        st.markdown("---")
        # ---------------- QUESTIONS ----------------
        if st.session_state.mcqs and not st.session_state.submitted and not st.session_state.auto_submitted:
            for idx, mcq in enumerate(st.session_state.mcqs):
                st.subheader(f"Q{idx + 1}. {mcq['question']}")
                st.session_state.user_answers[idx] = st.radio(
                    "Choose an option:",
                    ["a", "b", "c", "d"],
                    format_func=lambda x: f"{x}) {mcq['options'][x]}",
                    key=f"q_{idx}"
                )
        # ---------------- SUBMIT ----------------
            col1,col2,col3=st.columns([1.3,1,1])
            if col2.button("Submit Exam",type="primary"):
                score = 0
                total = len(st.session_state.mcqs)
                for idx, mcq in enumerate(st.session_state.mcqs):
                    if st.session_state.user_answers.get(idx) == mcq["correct_answer"]:
                        score += 1

                st.session_state.score = score
                st.session_state.total = total
                st.session_state.submitted = True

        # ---------------- AUTO SUBMIT ON VIOLATION ----------------
        if st.session_state.auto_submitted and not st.session_state.submitted:
            st.session_state.score = 0
            st.session_state.total = len(st.session_state.mcqs)
            st.session_state.submitted = True
            st.error("Exam auto-submitted due to violation. Score: 0")

        # ---------------- RESULT ----------------
        if st.session_state.submitted:
            st.success("✅ Exam Completed")
            #disaply number of correct and incorrect answers
            st.markdown(f"""
            <style>
            .crtanswers {{
                font-size: 18px;
                font-weight: bold;
                color: green;
            }}
            </style>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <style>
            .incrt-ans {{
                font-size: 18px;
                font-weight: bold;
                color: red;
            }}
            </style>
            """, unsafe_allow_html=True)
            st.markdown(f'<div class="crtanswers">Correct Answers: {st.session_state.score}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="incrt-ans">Incorrect Answers: {st.session_state.total - st.session_state.score}</div>', unsafe_allow_html=True)
            #add css to final score
            st.markdown(f"""
            <style>
            .final-score {{
                font-size: 24px;
                font-weight: bold;
                color: #4B0082;
            }}
            </style>
            """, unsafe_allow_html=True)
            st.markdown(f'<div class="final-score">Final Score: {st.session_state.score} / {st.session_state.total}</div>', unsafe_allow_html=True)

            percentage = (st.session_state.score / st.session_state.total) * 100
            if percentage >= 80:
                st.info("Excellent performance! 🎯")
            elif percentage >= 50:
                st.info("Good job! 👍")
            else:
                st.info("Needs improvement 📘")




elif st.session_state.page == "coding":

    with st.container(border=True):
        st.markdown(
        """
        <style>
        .center-title {

            text-align: center;
            font-size: 30px;
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: bold;
            color: #4B0082;
            margin-bottom: 16px;
        }
        </style>
        """, unsafe_allow_html=True
        )
        col1,col2=st.columns([12,1])
        col1.markdown(f'<div class="center-title">💻 {st.session_state.skill.upper()}- Coding Exam</div>', unsafe_allow_html=True)
    
        if col2.button("🏠"):
            st.session_state.page = "home"
            for key in [
                "coding_q_index",
                "coding_questions",
                "coding_scores",
                "coding_feedback",
                "coding_submitted",
                "last_result"
            ]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        # ---------------- SESSION INIT ----------------
        if "coding_q_index" not in st.session_state:
            st.session_state.coding_q_index = 0
            st.session_state.coding_questions = []
            st.session_state.coding_scores = []
            st.session_state.coding_feedback = []
            st.session_state.coding_submitted = False    

        # ---------------- START TEST ----------------
        if not st.session_state.coding_questions:
            col1,col2,col3=st.columns([1.4,1,1])
            if col2.button("Start Coding Test",type="primary"):
                with st.spinner("Preparing coding questions..."):
                    st.session_state.coding_questions = generate_coding_questions(
                        st.session_state.skill,
                        st.session_state.level
                    )
                st.rerun()
        #draw line
        st.markdown("---")
        # ---------------- QUESTION FLOW ----------------
        if st.session_state.coding_questions and not st.session_state.coding_submitted:

            idx = st.session_state.coding_q_index
            q = st.session_state.coding_questions[idx]

            st.subheader(f"Question {idx + 1} of 3")
            st.write(q["question"])

            st.caption(
                "⚠ Write Python code.\n"
                "Define a function named `solve(input_data)` "
                "that RETURNS the answer.\n"
                "No input(), no infinite loops."
            )

            code = st.text_area(
                "Write your code here:",
                height=260,
                key=f"user_code_{idx}",
                placeholder="def solve(input_data):\n    # Your code here\n    return result"
            )
            col1,col2,col3=st.columns([1,3.4,1])
            if col1.button("Run Code",type="primary"):
                with st.spinner("Evaluating code..."):
                    passed, msg = evaluate_code(code, q["test_cases"])

                if passed:
                    st.success(msg)
                else:
                    st.error(msg)

                st.session_state.last_result = passed

            if col3.button("Submit Code",type="primary"):
                if st.session_state.get("last_result"):
                    st.session_state.coding_scores.append(10)
                    st.session_state.coding_feedback.append("Correct solution")
                else:
                    st.session_state.coding_scores.append(0)
                    st.session_state.coding_feedback.append(
                        "Incorrect solution or runtime error"
                    )

                st.session_state.coding_q_index += 1
                st.session_state.last_result = False

                if st.session_state.coding_q_index == 3:
                    st.session_state.coding_submitted = True

                st.rerun()

        # ---------------- FINAL RESULT ----------------
        if st.session_state.coding_submitted:
            st.success("✅ Coding Test Completed!")
            st.markdown(f"""
                <style>
                .code {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #4B0082;
                }}
                </style>
            """, unsafe_allow_html=True)
            for i in range(3):
                st.markdown(
                    f"<div class='code'><b>Question {i + 1}: "
                    f"{st.session_state.coding_scores[i]} / 10 — "
                    f"{st.session_state.coding_feedback[i]}</div>"
                    , unsafe_allow_html=True
                )
            st.markdown(f"""
            <style>
            .final-score {{
                font-size: 24px;
                font-weight: bold;
                color: green;
            }}
            </style>
            """, unsafe_allow_html=True)

            final_score = sum(st.session_state.coding_scores)
            st.markdown(f'<div class="final-score">Final Score: {final_score} / 30</div>', unsafe_allow_html=True)

            if final_score >= 25:
                st.info("Excellent problem-solving skills!")
            elif final_score >= 15:
                st.info("Good logic, needs refinement.")
            else:
                st.info("Work on fundamentals and edge cases.")


elif st.session_state.page == "reasoning":
    with st.container(border=True):
        st.markdown(
        """
        <style>
        .center-title {

            text-align: center;
            font-size: 30px;
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: bold;
            color: #4B0082;
            margin-bottom: 16px;
        }
        </style>
        """, unsafe_allow_html=True
        )
        col1,col2=st.columns([12,1])
        col1.markdown(f'<div class="center-title">🧠Reasoning Test</div>', unsafe_allow_html=True)
        if col2.button("🏠"):
            st.session_state.page = "home"
            del st.session_state.reasoning_questions
            del st.session_state.reasoning_answers
            del st.session_state.reasoning_submitted
            del st.session_state.reasoning_score
            del st.session_state.skill
            del st.session_state.level
            st.rerun()
        # ---------------- INIT ----------------
        if "reasoning_questions" not in st.session_state:
            st.session_state.reasoning_questions = None
            st.session_state.reasoning_answers = {}
            st.session_state.reasoning_submitted = False
            st.session_state.reasoning_score = 0

        # ---------------- START BUTTON ----------------
        if st.session_state.reasoning_questions is None:
            col1,col2,col3=st.columns([1,1,1])
            if col2.button("Start Reasoning Test",type="primary"):
                with st.spinner("Generating questions..."):
                    st.session_state.reasoning_questions = generate_reasoning_questions()
                st.rerun()   # ✅ FIX 2
        #draw line
        st.markdown("---")
        # ---------------- DISPLAY QUESTIONS ----------------
        if st.session_state.reasoning_questions and not st.session_state.reasoning_submitted:

            tabs = st.tabs([f"Question {i+1}" for i in range(15)])

            for i in range(15):
                q = st.session_state.reasoning_questions[i]

                with tabs[i]:
                    st.markdown(f"### Question {i+1}")
                    st.write(q["question"])

                    st.session_state.reasoning_answers[i] = st.radio(
                        "Select an option:",
                        ["a", "b", "c", "d"],
                        format_func=lambda x: f"{x}) {q['options'][x]}",
                        key=f"reasoning_radio_{i}"
                    )

            if st.button("Submit Test",type="primary"):
                score = 0
                for i, q in enumerate(st.session_state.reasoning_questions):
                    if st.session_state.reasoning_answers.get(i) == q["answer"]:
                        score += 1

                st.session_state.reasoning_score = score
                st.session_state.reasoning_submitted = True
                st.rerun()

        # ---------------- RESULT ----------------
        if st.session_state.reasoning_submitted:

            st.success("🎉 Test Completed")
            # Question-wise feedback
            with st.expander("View Detailed Results"):
                for i, q in enumerate(st.session_state.reasoning_questions):
                    user_ans = st.session_state.reasoning_answers.get(i)
                    correct_ans = q["answer"]
                    #show question again
                    st.markdown(f"**Q{i+1}: {q['question']}**")
                    #show options
                    for opt in ["a", "b", "c", "d"]:
                        st.write(f"{opt}) {q['options'][opt]}")
                    if user_ans == correct_ans:
                        st.success(f"Q{i+1}: Correct ✅ (Your answer: {user_ans})")
                    else:
                        st.error(f"Q{i+1}: Wrong ❌ (Your answer: {user_ans} | Correct answer: {correct_ans})")
            #css for final score
            st.markdown(f"""
            <style>
            .final-score {{
                font-size: 24px;
                font-weight: bold;
                color: #4B0082;
            }}
            </style>
            """, unsafe_allow_html=True)
            st.markdown(f'<div class="final-score">Final Score: {st.session_state.reasoning_score} / 15</div>', unsafe_allow_html=True)

            percent = (st.session_state.reasoning_score / 15) * 100

            if percent >= 80:
                st.info("🔥 Excellent logical reasoning!")
            elif percent >= 50:
                st.info("👍 Good attempt, practice more.")
            else:
                st.info("📘 Needs improvement.")

elif st.session_state.page == "communication":
    with st.container(border=True):
        st.markdown(
        """
        <style>
        .center-title {

            text-align: center;
            font-size: 30px;
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: bold;
            color: #4B0082;
            margin-bottom: 16px;
        }
        </style>
        """, unsafe_allow_html=True
        )
        col1,col2=st.columns([12,1])
        col1.markdown(f'<div class="center-title">🗣️ Communication Skills Test</div>', unsafe_allow_html=True)
        if col2.button("🏠"):
            st.session_state.page = "home"
            del st.session_state.comm_scores
            del st.session_state.rec_texts
            del st.session_state.listening_done
            st.rerun()
        # ---------------- SESSION STATE INIT ----------------
        if "comm_scores" not in st.session_state:
            st.session_state.comm_scores = {
                "listening": [0]*3,
                "fill": [0]*3,
                "reading": 0,
                "topic": 0
            }
        else:
            # Ensure lists have proper lengths
            st.session_state.comm_scores["listening"] = st.session_state.comm_scores.get("listening", [0]*3)
            st.session_state.comm_scores["fill"] = st.session_state.comm_scores.get("fill", [0]*3)

        if "rec_texts" not in st.session_state:
            st.session_state.rec_texts = {
                "listening": [""]*3,
                "reading": "",
                "topic": ""
            }
        else:
            st.session_state.rec_texts["listening"] = st.session_state.rec_texts.get("listening", [""]*3)
            st.session_state.rec_texts["reading"] = st.session_state.rec_texts.get("reading", "")
            st.session_state.rec_texts["topic"] = st.session_state.rec_texts.get("topic", "")

        if "listening_done" not in st.session_state:
            st.session_state.listening_done = [False]*3
        else:
            st.session_state.listening_done = st.session_state.get("listening_done", [False]*3)
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        def text_similarity_score(user_text, expected_text):
            if not user_text.strip():
                return 0

            vectorizer = TfidfVectorizer()
            vectors = vectorizer.fit_transform([user_text, expected_text])

            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

            # Convert similarity (0–1) → score (0–10)
            return round(similarity * 10, 2)


        # ---------------- AUDIO RECORDER ----------------
        class AudioRecorder(AudioProcessorBase):
            def __init__(self, q):
                self.q = q

            def recv(self, frame):
                data = frame.to_ndarray()
                self.q.put(data)
                return frame

        def record_voice(section, idx=None, expected_text=None):
            q = queue.Queue()

            webrtc_streamer(
                key=f"{section}_{idx}",
                audio_processor_factory=lambda: AudioRecorder(q),
                media_stream_constraints={"audio": True, "video": False},
                async_processing=True
            )

            st.info("🎙️ Recording... Speak now!")

            if st.button(f"⏹ Stop Recording", key=f"stop_{section}_{idx}"):

                # ⛔ PLACEHOLDER (Replace later with real speech-to-text)
                recorded_text = f"Student spoke for {section} question {idx}"

                if section == "listening" and idx is not None:
                    score = text_similarity_score(recorded_text, expected_text)

                    st.session_state.rec_texts["listening"][idx] = recorded_text
                    st.session_state.comm_scores["listening"][idx] = score
                    st.session_state.listening_done[idx] = True

                    st.success(f"Score: {score} / 10")

                elif section == "reading":
                    st.session_state.rec_texts["reading"] = recorded_text
                    # generate score
                    score = text_similarity_score(recorded_text, expected_text)
                    st.session_state.comm_scores["reading"] = score
                    st.success(f"Score: {score} / 10")

                elif section == "topic":
                    st.session_state.rec_texts["topic"] = recorded_text
                    score = text_similarity_score(recorded_text, expected_text)
                    st.session_state.comm_scores["topic"] = score
                    st.success(f"Score: {score} / 10")


        # ---------------- TABS ----------------
        tabs = st.tabs([
            "🎧 Listening & Speaking",
            "✍ Fill in the Blanks",
            "📖 Paragraph Reading",
            "🎤 Topic Speaking"
        ])

        # ---------------- Listening & Speaking ----------------
        #need llm to generate questions
        listening_questions = generate_listening_questions()

        with tabs[0]:
            st.subheader("Listening & Speaking")
            for i, q_text in enumerate(listening_questions):
                st.markdown(f"**Q{i+1}: Listen and repeat**")
                st.write(q_text)
                if not st.session_state.listening_done[i]:
                    record_voice("listening", i,expected_text=q_text)
                else:
                    st.success("✅ Completed")

        # ---------------- Fill in the Blanks ----------------
        #need llm to generate blanks
        
        if "fill_questions" not in st.session_state:
            st.session_state.fill_questions = generate_fill_in_blanks()

        if "fill_answers" not in st.session_state:
            st.session_state.fill_answers = [""] * 5

        if "fill_scores" not in st.session_state:
            st.session_state.fill_scores = [0] * 5

        if "fill_submitted" not in st.session_state:
            st.session_state.fill_submitted = False
        with tabs[1]:
            st.subheader("✍ Fill in the Blanks")
            blanks = st.session_state.fill_questions

            for i, (sentence, answer) in enumerate(blanks):
                st.markdown(f"**Q{i+1}.** {sentence.replace('___', '______')}")
                st.session_state.fill_answers[i] = st.text_input(
                    "Your Answer",
                    key=f"fill_ans_{i}"
                )

            # SUBMIT BUTTON
            if st.button("✅ Submit", type="primary"):
                total = 0
                for i, (sentence, correct) in enumerate(blanks):
                    user = st.session_state.fill_answers[i].strip().lower()
                    if user == correct.lower():
                        st.session_state.fill_scores[i] = 10
                        total += 10
                    else:
                        st.session_state.fill_scores[i] = 0

                st.session_state.fill_submitted = True
                st.rerun()
            if st.session_state.fill_submitted:
                st.markdown("### 📊 Results")
                with st.expander("View Detailed Feedback"):
                    for i, (_, correct) in enumerate(st.session_state.fill_questions):
                        #show question again
                        st.markdown(f"**Q{i+1}: {st.session_state.fill_questions[i][0]}**")
                        st.write(f"Your Answer: {st.session_state.fill_answers[i]}")
                        score = st.session_state.fill_scores[i]
                        if score == 10:
                            st.success(f"Q{i+1}: Correct ✅ (10 / 10)")
                        else:
                            st.error(f"Q{i+1}: Wrong ❌ | Correct Answer: {correct}")
                #css for final score
                st.markdown(f"""
                    <style>
                    .final-score {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #4B0082;
                    }}
                    </style>
                """, unsafe_allow_html=True)
                st.markdown(f'<div class="final-score">Final Score: {sum(st.session_state.fill_scores)} / 50</div>', unsafe_allow_html=True)
                #remove questions and answers to prevent resubmission
                del st.session_state.fill_questions
                del st.session_state.fill_answers
                del st.session_state.fill_scores
                del st.session_state.fill_submitted

        # ---------------- Paragraph Reading ----------------
        #need llm to generate paragraph
        reading_paragraph = generate_reading_paragraph()

        with tabs[2]:
            st.subheader("Paragraph Reading")
            st.write(reading_paragraph)
            record_voice("reading",idx=None,expected_text=reading_paragraph)

        # ---------------- Topic Speaking ----------------
        
        topic = generate_topic()

        with tabs[3]:
            st.subheader("Topic Speaking")
            st.write(f"🎯 **Topic:** {topic}")
            record_voice("topic",idx=None,expected_text=topic)

        # ---------------- FINAL SUBMIT ----------------
else:
    st.error("Unknown page. Returning to home.")
    st.session_state.page = "home"
    st.rerun()