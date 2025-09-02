import streamlit as st
import speech_recognition as sr
import ollama
import json
import re

st.set_page_config(page_title="AI Interview Practice", page_icon="🎤", layout="centered")

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/microphone.png", width=80)
    st.title("AI Interview Practice")
    st.markdown("Welcome! Practice your interview skills with voice or text. Get instant feedback at the end. Good luck! 🍀")
    st.markdown("---")
    st.info("Tip: Click 'Speak Answer' and allow microphone access.")

# Role Selection
roles = {
    "Software Engineer": [
        "Tell me about a coding project you’re proud of.",
        "How do you approach debugging complex code?",
        "What programming languages are you most comfortable with?",
        "Explain a time you had to optimize a piece of code.",
        "How do you keep up with new technologies?"
    ],
    "Product Manager": [
        "How do you prioritize features in a product roadmap?",
        "Tell me about a successful product you managed.",
        "How do you handle conflicts between stakeholders?",
        "Describe your process for user research.",
        "What KPIs do you typically track for a new product?"
    ],
    "Data Analyst": [
        "Tell me about a time you turned data into actionable insights.",
        "What tools do you use for data visualization?",
        "How do you handle missing or inconsistent data?",
        "Explain a complex analysis you’ve conducted.",
        "How do you validate the accuracy of your results?"
    ]
}

if 'selected_role' not in st.session_state:
    st.session_state.selected_role = None

# Initial role selection before starting
if st.session_state.selected_role is None:
    st.markdown("<h1 style='text-align: center;'>🎓 Select Interview Role</h1>", unsafe_allow_html=True)
    selected = st.selectbox("Choose the role you want to practice:", list(roles.keys()))
    if st.button("Start Interview"): 
        st.session_state.selected_role = selected
        st.session_state.questions = roles[selected]
        st.session_state.index = 0
        st.session_state.answers = []
        st.session_state.current_text = ""
        st.rerun()
    st.stop()

questions = st.session_state.questions

# Evaluation Prompt
OLLAMA_PROMPT_TEMPLATE = """
You are an AI Interview Evaluator. Evaluate the candidate's answer to the interview question below.

Question: {question}
Answer: {answer}

Return only a JSON object with these fields:
{{
  "relevance": Integer score from 1 to 10,
  "clarity": Integer score from 1 to 10,
  "confidence": Integer score from 1 to 10,
  "grammar": Integer score from 1 to 10,
  "overall_feedback": Short feedback (2–3 lines)
}}
"""

# @st.cache_data(show_spinner=False)
# def evaluate_answer_ollama(question, answer):
#     prompt = OLLAMA_PROMPT_TEMPLATE.format(question=question, answer=answer)
#     try:
#         response = ollama.chat(model="llama3:8b", messages=[{"role": "user", "content": prompt}])
#         content = response['message']['content']
#         match = re.search(r"\{[\s\S]*\}", content)
#         if match:
#             return json.loads(match.group(0))
#         else:
#             raise ValueError("No JSON object found.")
#     except Exception as e:
#         st.error("\u26a0\ufe0f Couldn't parse model output as JSON.")
#         st.text_area("Raw Output", response.get('message', {}).get('content', ''), height=200)
#         return {"error": str(e), "raw": ""}
@st.cache_data(show_spinner=False)
def evaluate_answer_ollama(question, answer):
    prompt = OLLAMA_PROMPT_TEMPLATE.format(question=question, answer=answer)
    response = None  # ensure it's defined even if something fails

    try:
        response = ollama.chat(model="llama3:8b", messages=[{"role": "user", "content": prompt}])
        content = response['message']['content']

        # Extract JSON-like portion
        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            json_str = match.group(0)
            json_str = re.sub(r'//.*', '', json_str)  # remove comments
            return json.loads(json_str)
        else:
            raise ValueError("No JSON object found.")

    except Exception as e:
        st.error(f"⚠️ Couldn't parse model output as JSON: {e}")

        raw_content = ""
        if response and 'message' in response:
            raw_content = response['message'].get('content', '')

        st.text_area("Raw Output", raw_content, height=200)
        return {"error": str(e), "raw": raw_content}

# Header
st.markdown(f"<h1 style='text-align: center; color: #4F8BF9;'>🎤 {st.session_state.selected_role} Interview Practice</h1>", unsafe_allow_html=True)
progress = st.session_state.index / len(questions)
st.progress(progress)

if st.session_state.index < len(questions):
    current_q = questions[st.session_state.index]
    st.markdown(f"<h3 style='color:#6C3483;'>❓ Question {st.session_state.index+1} of {len(questions)}:</h3>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:20px; margin-bottom:10px;'><b>{current_q}</b></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🎧 Speak Answer"):
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                st.toast("Listening...", icon="🎤")
                audio = recognizer.listen(source, phrase_time_limit=7)
            try:
                text = recognizer.recognize_google(audio)
                st.session_state.current_text = text
                st.toast("Transcribed!", icon="✅")
                st.success(f"You said: {text}")
            except sr.UnknownValueError:
                st.warning("Sorry, could not understand your voice.")
            except sr.RequestError:
                st.error("Speech Recognition service failed.")

    with col2:
        st.session_state.current_text = st.text_input(
            "💬 Or type your answer below:",
            value=st.session_state.current_text,
            key=f"answer_input_{st.session_state.index}"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("➡ Next"):
        answer = st.session_state.current_text.strip()
        if answer:
            st.session_state.answers.append((current_q, answer))
            st.session_state.index += 1
            st.session_state.current_text = ""
            st.rerun()
        else:
            st.warning("Please provide an answer before proceeding.")
else:
    st.markdown("""
        <div style='text-align:center;'>
            <h2 style='color:#229954; font-size:2.2em;'>✨ You have completed the interview successfully! ✨</h2>
            <span style='font-size:3em;'>🎉🌟🎇</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='color:#229954;'>📝 Your Answers:</h2>", unsafe_allow_html=True)

    total_score = 0
    max_score = 0

    for i, (q, a) in enumerate(st.session_state.answers, 1):
        feedback = evaluate_answer_ollama(q, a)

        if "error" in feedback:
            st.error(f"Evaluation failed for Q{i}: {feedback['error']}")
            st.text(feedback.get('raw', ''))
            continue

        st.markdown(f"**Q{i}:** {q}")
        st.markdown(f"**📝 A{i}:** {a}")
        st.markdown(f"- 📊 Scores: Relevance: {feedback['relevance']}, Clarity: {feedback['clarity']}, Confidence: {feedback['confidence']}, Grammar: {feedback['grammar']}")
        st.markdown(f"- 💡 Feedback: _{feedback['overall_feedback']}_")
        st.markdown("---")

        total_score += feedback['relevance'] + feedback['clarity'] + feedback['confidence'] + feedback['grammar']
        max_score += 40

    percent = (total_score / max_score) * 100 if max_score else 0
    st.markdown(f"## 🧠 Overall Interview Score: **{percent:.1f}%**")
    if percent >= 80:
        st.success("💪 Great job! You're well prepared.")
    elif percent >= 50:
        st.warning("🙂 Decent attempt. Review the suggestions above to improve.")
    else:
        st.error("⚠️ You need more preparation. Focus on clarity and relevance.")

    if st.button("🔁 Restart Interview"):
        st.session_state.selected_role = None
        st.session_state.index = 0
        st.session_state.answers = []
        st.session_state.current_text = ""
        st.rerun()
