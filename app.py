import streamlit as st
import pandas as pd
import requests
import json
import os
from io import BytesIO
from supabase import create_client, Client

# --- CONFIG FROM SECRETS ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Diagnostic Pro: Math & English", layout="wide")

# --- NAVIGATION ---
page = st.sidebar.radio("Navigation", ["Take Assessment", "Admin Dashboard"])

# --- AI AGENT FUNCTION ---
def generate_ai_report(tutor_name, student_name, subject, grade, curriculum, results_text, tutor_feedback):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"Analyze results for {student_name} ({subject}, {grade}). Results: {results_text}. Tutor: {tutor_feedback}. Task: 1. Diagnostic Report. 2. 12-Week Online Plan (Markdown Table)."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except: return "AI Plan generation failed."

# --- IMAGE LOADER ---
def display_img(url, w=450, return_bytes=False):
    if not url or not isinstance(url, str) or len(url) < 10: return None
    try:
        f_url = url
        if 'drive.google.com' in url:
            f_id = url.split('/file/d/')[1].split('/')[0] if '/file/d/' in url else url.split('id=')[1].split('&')[0]
            f_url = f'https://drive.google.com/uc?export=download&id={f_id}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(f_url, headers=headers, timeout=12)
        if res.status_code == 200:
            img_data = BytesIO(res.content)
            if return_bytes: return img_data
            else: st.image(img_data, width=w); return True
    except: return None

# --- DATABASE LOGIC ---
def save_to_supabase(data):
    try:
        supabase.table("assessment_results").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

# --- DATA LOADER ---
def load_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f: return json.load(f)
    return {}
ALL_DATA = load_data()

# --- ADMIN DASHBOARD ---
if page == "Admin Dashboard":
    st.title("📊 Admin Result Dashboard")
    # Fetch data from Supabase
    res = supabase.table("assessment_results").select("*").order("created_at", desc=True).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        # Clean up view
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(df[['created_at', 'tutor', 'student', 'subject', 'grade', 'curriculum']], use_container_width=True)
        
        # Detail Viewer
        st.divider()
        selected_student = st.selectbox("View full report for:", df['student'].unique())
        student_data = df[df['student'] == selected_student].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Diagnostic Results")
            st.text(student_data['results'])
            st.subheader("Tutor Feedback")
            st.write(student_data['feedback'])
        with col2:
            st.subheader("AI 12-Week Plan")
            st.markdown(student_data['ai_plan'])
    else:
        st.info("No assessments found in database.")

# --- ASSESSMENT FLOW ---
elif page == "Take Assessment":
    if 'step' not in st.session_state:
        st.session_state.update({"step": "setup", "results": [], "set_idx": 0, "sub_idx": 0, "phase": "familiarity", "mastery_count": 0, "perfect_score": True, "bottleneck_active": False, "ai_report": ""})

    if st.session_state.step == "setup":
        st.title("Diagnostic Setup")
        subjs = list(ALL_DATA.keys())
        s_subj = st.selectbox("Select Subject", subjs) if subjs else None
        if s_subj:
            currs = list(ALL_DATA[s_subj].keys())
            s_curr = st.selectbox("Select Curriculum", currs)
            if s_curr:
                grades = list(ALL_DATA[s_subj][s_curr].keys())
                s_grade = st.selectbox("Select Starting Grade", grades)
        t_tutor, t_student = st.text_input("Tutor Name"), st.text_input("Student Name")
        if st.button("Begin"):
            st.session_state.update({"p_tutor": t_tutor, "p_student": t_student, "p_subject": s_subj, "p_curr": s_curr, "p_grade": s_grade, "step": "testing"})
            st.rerun()

    elif st.session_state.step == "testing":
        subj, grade = st.session_state.p_subject, st.session_state.p_grade
        content = ALL_DATA[subj][st.session_state.p_curr][grade]
        current_set = content[st.session_state.set_idx]
        st.title(f"{subj}: {grade}")
        
        if st.session_state.phase == "familiarity":
            topic_lbl = current_set.get('topic') or current_set.get('section_title')
            st.header(topic_lbl)
            st.subheader("Is the student familiar with this?")
            c1, c2 = st.columns([1, 5])
            if c1.button("Yes"): st.session_state.phase = "content"; st.rerun()
            if c2.button("No"):
                st.session_state.results.append({"Grade": grade, "Topic": topic_lbl, "Status": "Not Familiar"})
                if st.session_state.bottleneck_active: st.session_state.step = "summary"
                else: 
                    if st.session_state.set_idx < len(content)-1: st.session_state.set_idx += 1; st.session_state.phase = "familiarity"
                    else: st.session_state.step = "summary"
                st.rerun()

        elif st.session_state.phase in ["content", "mastery_retry", "subs"]:
            if subj == "Mathematics":
                # [KEEP ORIGINAL MATH LOGIC HERE - PRESERVED FOR BREVITY]
                if st.session_state.phase in ["content", "mastery_retry"]:
                    lbl = "Mastery Q" if st.session_state.phase == "content" else "Mastery Q (Retry)"
                    st.info(current_set['mastery_q'])
                    display_img(current_set.get('image') or current_set.get('mastery_image'))
                    if st.button("✅ Correct"):
                        st.session_state.results.append({"Grade": grade, "Topic": current_set['topic'], "Status": "Correct"})
                        st.session_state.mastery_count += 1
                        if st.session_state.set_idx < len(content)-1: st.session_state.set_idx += 1; st.session_state.phase = "familiarity"
                        else: st.session_state.step = "summary"
                        st.rerun()
                    if st.button("❌ Incorrect"):
                        st.session_state.phase = "subs"; st.session_state.sub_idx = 0; st.rerun()
                elif st.session_state.phase == "subs":
                    sub = current_set['subs'][st.session_state.sub_idx]
                    st.write(sub['q'])
                    if st.button("Next Correct"):
                        if st.session_state.sub_idx < len(current_set['subs'])-1: st.session_state.sub_idx += 1
                        else: st.session_state.phase = "mastery_retry"
                        st.rerun()
            else: # ENGLISH LOGIC
                section = current_set
                st.info(section['instruction'])
                if section.get('content_text'): st.code(section['content_text'])
                q = section['questions'][st.session_state.sub_idx]
                st.subheader(q['q'])
                if st.button("✅ Correct"):
                    st.session_state.results.append({"Grade": grade, "Topic": section['section_title'], "Status": "Correct"})
                    if st.session_state.sub_idx < len(section['questions'])-1: st.session_state.sub_idx += 1
                    elif st.session_state.set_idx < len(content)-1: st.session_state.set_idx += 1; st.session_state.sub_idx = 0; st.session_state.phase = "familiarity"
                    else: st.session_state.step = "summary"
                    st.rerun()
                if st.button("❌ Incorrect"):
                    st.session_state.step = "summary"; st.rerun()

    elif st.session_state.step == "summary":
        st.title("Summary")
        df = pd.DataFrame(st.session_state.results)
        st.table(df)
        obs = st.text_area("Tutor Feedback")
        if st.button("✨ Generate AI Plan"):
            st.session_state.ai_report = generate_ai_report(st.session_state.p_tutor, st.session_state.p_student, st.session_state.p_subject, st.session_state.p_grade, st.session_state.p_curr, df.to_string(), obs)
            st.markdown(st.session_state.ai_report)
        if st.button("💾 Save to Supabase"):
            payload = {
                "tutor": st.session_state.p_tutor, "student": st.session_state.p_student,
                "subject": st.session_state.p_subject, "curriculum": st.session_state.p_curr,
                "grade": st.session_state.p_grade, "results": df.to_string(),
                "feedback": obs, "ai_plan": st.session_state.ai_report
            }
            if save_to_supabase(payload): st.success("Saved to Database!")
