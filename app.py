import streamlit as st
import pandas as pd
import requests
import json
import os
import re
from io import BytesIO
from supabase import create_client, Client

# --- CONFIG FROM SECRETS ---
def get_secret(key):
    return st.secrets.get(key.upper()) or st.secrets.get(key.lower())

SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD")

st.set_page_config(page_title="Multi-Subject Diagnostic Pro", layout="wide")

# --- INITIALIZE SUPABASE ---
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        url = SUPABASE_URL.strip().rstrip("/")
        key = SUPABASE_KEY.strip()
        return create_client(url, key)
    except:
        return None

supabase = init_supabase()

# --- AI AGENT FUNCTION ---
def generate_ai_report(tutor_name, student_name, subject, grade, curriculum, results_text, tutor_feedback):
    if not GEMINI_API_KEY: return "AI Error: Gemini Key missing in Secrets."
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"Expert Diagnostician: Analyze {student_name} results for {subject} ({grade} - {curriculum}). Results: {results_text}. Tutor Notes: {tutor_feedback}. Task: 1. Diagnostic Performance Overview. 2. 12-Week Personal Plan table."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"AI Plan generation failed: {str(e)}"

# --- UNIVERSAL IMAGE LOADER ---
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

# --- DATA LOADER ---
def load_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f: return json.load(f)
    return {}
ALL_DATA = load_data()

# --- STATE MGMT ---
if 'step' not in st.session_state:
    st.session_state.update({
        "step": "setup", "results": [], "set_idx": 0, "sub_idx": 0, 
        "phase": "familiarity", "mastery_count": 0, "perfect_score": True, 
        "bottleneck_active": False, "ai_report": "", "admin_authenticated": False
    })

def record(subj, grade, topic, level, status):
    st.session_state.results.append({"Subject": subj, "Grade": grade, "Topic": topic, "Level": level, "Status": status})

def advance_logic():
    subj = st.session_state.p_subject
    grade_data = ALL_DATA[subj][st.session_state.p_curr][st.session_state.p_grade]
    all_grades = list(ALL_DATA[subj][st.session_state.p_curr].keys())
    g_idx = all_grades.index(st.session_state.p_grade)

    if subj == "Mathematics":
        if st.session_state.set_idx < len(grade_data) - 1:
            st.session_state.set_idx += 1; st.session_state.sub_idx = 0; st.session_state.phase = "familiarity"
        else:
            if st.session_state.mastery_count >= len(grade_data) and g_idx < len(all_grades) - 1:
                st.session_state.p_grade = all_grades[g_idx + 1]
                st.session_state.set_idx = 0; st.session_state.sub_idx = 0; st.session_state.mastery_count = 0
                st.session_state.phase = "familiarity"; st.session_state.bottleneck_active = True
                st.toast(f"Leveling up to {st.session_state.p_grade}!", icon="🚀")
            else: st.session_state.step = "summary"
    else:
        if st.session_state.sub_idx < len(grade_data[st.session_state.set_idx]['questions']) - 1:
            st.session_state.sub_idx += 1
        elif st.session_state.set_idx < len(grade_data) - 1:
            st.session_state.set_idx += 1; st.session_state.sub_idx = 0; st.session_state.phase = "familiarity"
        else:
            if st.session_state.perfect_score and g_idx < len(all_grades) - 1:
                st.session_state.p_grade = all_grades[g_idx + 1]
                st.session_state.set_idx = 0; st.session_state.sub_idx = 0
                st.session_state.phase = "familiarity"; st.session_state.perfect_score = True
                st.session_state.bottleneck_active = True
                st.toast(f"Leveling up to {st.session_state.p_grade}!", icon="📚")
            else: st.session_state.step = "summary"
    st.rerun()

# --- NAVIGATION ---
page = st.sidebar.radio("Navigation", ["Take Assessment", "Admin Dashboard"])

# --- ADMIN DASHBOARD (PASSWORD PROTECTED) ---
if page == "Admin Dashboard":
    st.title("📊 Admin Dashboard")
    
    if not st.session_state.admin_authenticated:
        # Login Form
        pwd_input = st.text_input("Enter Admin Secret Key", type="password")
        if st.button("Unlock Dashboard"):
            if pwd_input == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect Secret Key")
    else:
        # Dashboard Content
        if st.sidebar.button("Logout Admin"):
            st.session_state.admin_authenticated = False
            st.rerun()
            
        if not supabase:
            st.warning("Database configuration missing.")
        else:
            try:
                res = supabase.table("assessment_results").select("*").order("created_at", desc=True).execute()
                if res.data:
                    df = pd.DataFrame(res.data)
                    st.dataframe(df[['created_at', 'tutor', 'student', 'subject', 'grade']], use_container_width=True)
                    st.divider()
                    sel_student = st.selectbox("View Detailed Report for:", df['student'].unique())
                    row = df[df['student'] == sel_student].iloc[0]
                    c1, c2 = st.columns(2)
                    with c1: 
                        st.subheader("Diagnostic Results")
                        st.text(row['results'])
                        st.subheader("Feedback")
                        st.write(row['feedback'])
                    with c2: 
                        st.subheader("AI Personalized Plan")
                        st.markdown(row['ai_plan'])
                else: st.info("No records found.")
            except Exception as e:
                st.error(f"Error fetching data: {e}")

# --- ASSESSMENT FLOW ---
elif page == "Take Assessment":
    # Sidebar Status (for tutors)
    with st.sidebar:
        if supabase: st.success("✅ Database Connected")
        else: st.error("❌ Database Offline")

    if st.session_state.step == "setup":
        st.title("Diagnostic Setup")
        subjs = list(ALL_DATA.keys())
        s_subj = st.selectbox("Subject", subjs) if subjs else None
        if s_subj:
            currs = list(ALL_DATA[s_subj].keys())
            s_curr = st.selectbox("Curriculum", currs)
            if s_curr:
                grades = list(ALL_DATA[s_subj][s_curr].keys())
                s_grade = st.selectbox("Starting Grade", grades)
        t_tutor, t_student = st.text_input("Tutor Name"), st.text_input("Student Name")
        if st.button("Begin"):
            if t_tutor and t_student and s_grade:
                st.session_state.update({"p_tutor": t_tutor, "p_student": t_student, "p_subject": s_subj, "p_curr": s_curr, "p_grade": s_grade, "p_start_grade": s_grade, "step": "testing"})
                st.rerun()

    elif st.session_state.step == "testing":
        subj, grade = st.session_state.p_subject, st.session_state.p_grade
        content = ALL_DATA[subj][st.session_state.p_curr][grade]
        current_set = content[st.session_state.set_idx]
        st.title(f"{subj}: {grade}"); st.divider()

        if st.session_state.phase == "familiarity":
            topic_lbl = current_set.get('topic') or current_set.get('section_title')
            st.header(topic_lbl)
            st.subheader("Is the student familiar with this?")
            c1, c2 = st.columns([1, 5])
            if c1.button("Yes"): st.session_state.phase = "content"; st.rerun()
            if c2.button("No"):
                record(subj, grade, topic_lbl, "Familiarity", "No"); st.session_state.perfect_score = False
                if st.session_state.bottleneck_active: st.session_state.step = "summary"
                else: advance_logic()
                st.rerun()

        elif st.session_state.phase in ["content", "mastery_retry", "subs"]:
            if subj == "Mathematics":
                if st.session_state.phase in ["content", "mastery_retry"]:
                    lbl = "Mastery Q" if st.session_state.phase == "content" else "Mastery Q (Retry)"
                    st.info(current_set['mastery_q'])
                    display_img(current_set.get('image') or current_set.get('mastery_image'))
                    if st.checkbox("Show Hint"): st.warning(current_set['mastery_hint'])
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Correct"):
                        record(subj, grade, current_set['topic'], lbl, "Correct"); st.session_state.mastery_count += 1; advance_logic()
                    if c1.button("❌ Incorrect"):
                        record(subj, grade, current_set['topic'], lbl, "Incorrect"); st.session_state.perfect_score = False
                        if st.session_state.bottleneck_active or st.session_state.phase == "mastery_retry": st.session_state.step = "summary"
                        else: st.session_state.phase = "subs"; st.session_state.sub_idx = 0
                        st.rerun()
                elif st.session_state.phase == "subs":
                    sub = current_set['subs'][st.session_state.sub_idx]
                    st.subheader(f"Sub-Q {st.session_state.sub_idx+1}"); st.write(sub['q']); display_img(sub.get('image'))
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Correct"):
                        record(subj, grade, current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Correct")
                        if st.session_state.sub_idx < len(current_set['subs'])-1: st.session_state.sub_idx += 1; st.rerun()
                        else: st.session_state.phase = "mastery_retry"; st.rerun()
                    if c2.button("❌ Incorrect"):
                        record(subj, grade, current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Incorrect"); st.session_state.perfect_score = False
                        if st.session_state.bottleneck_active: st.session_state.step = "summary"
                        else: advance_logic()
                        st.rerun()
            else:
                st.info(f"**Instruction:** {current_set['instruction']}")
                if current_set.get('content_text'): st.code(current_set['content_text'])
                display_img(current_set.get('image') or current_set.get('mastery_image'))
                q = current_set['questions'][st.session_state.sub_idx]
                st.subheader(q['q'])
                imgs = q.get('images') or []
                if isinstance(imgs, list) and imgs:
                    cols = st.columns(len(imgs))
                    for i, u in enumerate(imgs):
                        b = display_img(u, return_bytes=True)
                        if b: cols[i].image(b, use_container_width=True)
                elif q.get('image'): display_img(q.get('image'))
                
                c1, c2 = st.columns(2)
                if c1.button("✅ Correct"): record(subj, grade, current_set['section_title'], f"Q{st.session_state.sub_idx+1}", "Correct"); advance_logic()
                if c2.button("❌ Incorrect"):
                    record(subj, grade, current_set['section_title'], f"Q{st.session_state.sub_idx+1}", "Incorrect"); st.session_state.perfect_score = False
                    if st.session_state.bottleneck_active: st.session_state.step = "summary"
                    else: advance_logic()
                    st.rerun()

    elif st.session_state.step == "summary":
        st.title("Assessment Summary")
        df = pd.DataFrame(st.session_state.results); st.table(df)
        obs = st.text_area("Tutor Observations")
        if st.button("✨ Generate AI Plan"):
            with st.spinner("AI is analyzing performance..."):
                st.session_state.ai_report = generate_ai_report(st.session_state.p_tutor, st.session_state.p_student, st.session_state.p_subject, st.session_state.p_grade, st.session_state.p_curr, df.to_string(), obs)
            st.markdown(st.session_state.ai_report)
        
        if st.button("💾 Save Results to Admin Dashboard"):
            if not supabase: st.error("Database connection failed.")
            else:
                try:
                    payload = {"tutor": st.session_state.p_tutor, "student": st.session_state.p_student, "subject": st.session_state.p_subject, "curriculum": st.session_state.p_curr, "grade": st.session_state.p_grade, "results": df.to_string(), "feedback": obs, "ai_plan": st.session_state.ai_report}
                    supabase.table("assessment_results").insert(payload).execute()
                    st.success("Results saved successfully!")
                except Exception as e: st.error(f"Save failed: {e}")
