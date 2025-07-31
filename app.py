import streamlit as st
import datetime
import json
import hashlib
from pathlib import Path
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# --- CONFIGURATION ---
st.set_page_config(page_title="AI Study Planner", layout="wide")
st.title("📚 Personalized AI Study Planner")

# --- AUTHENTICATION HELPERS ---
USERS_FILE = Path("users.json")
if not USERS_FILE.exists():
    USERS_FILE.write_text("{}")

def load_users():
    with USERS_FILE.open() as f:
        return json.load(f)

def save_users(users):
    with USERS_FILE.open("w") as f:
        json.dump(users, f)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# --- SIDEBAR AUTH ---
st.sidebar.header("🔐 Account")
auth_mode = st.sidebar.radio("Select action", ["Login", "Sign Up"])

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if auth_mode == "Sign Up":
    reg_email = st.sidebar.text_input("Email", key="signup_email")
    reg_pw = st.sidebar.text_input("Password", type="password", key="signup_pw")
    reg_pw2 = st.sidebar.text_input("Confirm Password", type="password", key="signup_pw2")
    if st.sidebar.button("Create Account"):
        users = load_users()
        if reg_email in users:
            st.sidebar.error("Email already registered.")
        elif reg_pw != reg_pw2:
            st.sidebar.error("Passwords do not match.")
        else:
            users[reg_email] = hash_password(reg_pw)
            save_users(users)
            st.sidebar.success("Account created. You can now log in.")
else:  # Login
    log_email = st.sidebar.text_input("Email", key="login_email")
    log_pw = st.sidebar.text_input("Password", type="password", key="login_pw")
    if st.sidebar.button("Login"):
        users = load_users()
        if log_email in users and users[log_email] == hash_password(log_pw):
            st.session_state.logged_in = True
            st.session_state.user_email = log_email
            st.sidebar.success(f"Logged in as {log_email}")
        else:
            st.sidebar.error("Invalid credentials.")

if not st.session_state.logged_in:
    st.info("Please log in to use the planner.")
    st.stop()

# --- GEMINI API SETUP ---
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    st.session_state.gemini_model = genai.GenerativeModel("gemini-2.-flash")

# --- SESSION STATE SETUP ---
if "plan" not in st.session_state:
    st.session_state.plan = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- MAIN FORM: STUDY INPUT ---
st.subheader("📝 Enter Exam Details")
with st.form("study_form"):
    exam_name = st.text_input("Exam Name")
    exam_date = st.date_input("Exam Date", min_value=datetime.date.today())
    strengths = st.text_area("Your Strengths (Subjects or Topics)")
    weaknesses = st.text_area("Your Weaknesses (Subjects or Topics)")
    free_time = st.slider("How many hours per day can you study?", 1, 10, 3)
    submitted = st.form_submit_button("Generate Study Plan")

if submitted and api_key:
    prompt = f"""
    You are a study planner. Today is {datetime.date.today()}.
    I have an exam called {exam_name} on {exam_date}.
    My strengths: {strengths}.
    My weaknesses: {weaknesses}.
    I can study {free_time} hours daily.
    Make a study plan breaking down what I should study each day, starting tomorrow.
    Keep it clear, structured, and easy to follow.
    Output as bullet points for each day with subject/topic/time.
    Also, provide a short motivational tip at the end.
    """

    response = st.session_state.gemini_model.generate_content(prompt)
    st.session_state.plan = response.text
    st.success("✅ Study Plan Generated!")
    st.markdown(st.session_state.plan)

    # Save user plan locally
    user_email = st.session_state.user_email
    user_data = {
        "email": user_email,
        "exam_name": exam_name,
        "exam_date": str(exam_date),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "plan": st.session_state.plan,
    }
    with open(f"user_data_{user_email}.json", "w") as f:
        json.dump(user_data, f)

# --- DAILY TODO DISPLAY ---
if st.session_state.plan:
    st.subheader("✅ Daily Study To-Dos")
    todos = [line for line in st.session_state.plan.splitlines() if line.strip().startswith("•") or line.strip().startswith("-")]
    for idx, todo in enumerate(todos):
        st.checkbox(todo.strip(), key=f"todo_{idx}")

# --- AI CHAT FOLLOW-UP ---
st.subheader("🤖 Ask AI About Your Plan")
user_input = st.text_input("Ask something (e.g., What to do next?)")
if st.button("Ask") and user_input and api_key:
    st.session_state.messages.append({"role": "user", "content": user_input})
    full_chat = [msg["content"] for msg in st.session_state.messages if msg["role"] == "user"]
    chat = st.session_state.gemini_model.start_chat()
    for q in full_chat:
        chat.send_message(q)
    reply = chat.last.text
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").markdown(reply)

# --- SHOW CHAT HISTORY ---
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).markdown(msg["content"])
