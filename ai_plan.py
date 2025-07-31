# ai_plan.py
from datetime import datetime, timedelta
from typing import List
import google.generativeai as genai

def setup_gemini(api_key: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-pro")

def generate_plan(model, exam_name, exam_date, strengths, weaknesses):
    prompt = f"""
You are a smart AI tutor. Generate a personalized daily study plan for the exam "{exam_name}" scheduled on {exam_date}.

- Focus more on these weak subjects/topics: {weaknesses}
- Spend less time on: {strengths}
- Spread the topics equally till exam day.
- Include one or two specific topics per day.
- Output each day like: "Day 1 - Maths: Algebra, Physics: Kinematics"

Only return the daily breakdown in a numbered list.
    """
    response = model.generate_content(prompt)
    return response.text
