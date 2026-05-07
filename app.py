import streamlit as st
import pandas as pd
import requests
import json
import os
from io import BytesIO

# --- CONFIG ---
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyZU-Km741xhQuKc9W98-xFGsaEQ18P2LgRKlCSNEKZDzYoXrqgpEA04WMoFLeq_WRpFQ/exec" 

st.set_page_config(page_title="Multi-Subject Diagnostic", layout="wide")

@st.cache_data
def load_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f:
            return json.load(f)
    return {}

ALL_DATA = load_data()

# --- IMAGE LOADER ---
def display_img(url, w=400):
    if not url or not isinstance(url, str) or len(url) < 10: return
    try:
        f_url = url
        if 'drive.google.com' in url:
            f_id = url.split('/file/d/')[1].split('/')[0] if '/file/d/' in url else url.split('id=')[1].split('&')[0]
            f_url = f'https://drive.google.com/uc?export=download&id={f_id}'
        res = requests.get(f_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if res.status_code == 200: st.image(BytesIO(res.content), width=w)
    except: pass

# --- STATE MGMT ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.results = []
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    st.session_state.phase = "familiarity"
    st.session_state.mastery_count = 0
    st.session_state.bottleneck = False

def record(subj, grade, topic, q, status):
    st.session_state.results.append({"Subject": subj, "Grade": grade, "Topic": topic, "Question": q, "Status": status})

# --- SETUP SCREEN ---
if st.session_state.step == "setup":
    st.title("Diagnostic Assessment Setup")
    
    if not ALL_DATA:
        st.error("Wait! content.json is empty or formatted incorrectly.")
        st.stop()

    # 1. Select Subject (Math or English)
    subjs = list(ALL_DATA.keys())
    s_subj = st.selectbox("Select Subject", subjs)

    # 2. Select Curriculum (e.g., US Common Core)
    currs = list(ALL_DATA[s_subj].keys()) if s_subj else []
    s_curr = st.selectbox("Select Curriculum", currs)

    # 3. Select Grade (e.g., Kindergarten)
    # We use .get() and check if it's a dict to prevent the AttributeError in your screenshot
    grade_options = []
    if s_subj and s_curr:
        data_at_curr = ALL_DATA[s_subj].get(s_curr, {})
        if isinstance(data_at_curr, dict):
            grade_options = list(data_at_curr.keys())
    
    s_grade = st.selectbox("Select Grade/Class", grade_options)

    t_tutor = st.text_input("Tutor Name")
    t_student = st.text_input("Student Name")

    if st.button("Start Assessment"):
        if t_tutor and t_student and s_grade:
            st.session_state.p_tutor = t_tutor
            st.session_state.p_student = t_student
            st.session_state.p_subject = s_subj
            st.session_state.p_curr = s_curr
            st.session_state.p_grade = s_grade
            st.session_state.step = "testing"
            st.rerun()

# --- TESTING SCREEN ---
elif st.session_state.step == "testing":
    subj = st.session_state.p_subject
    grade = st.session_state.p_grade
    content = ALL_DATA[subj][st.session_state.p_curr][grade]
    
    st.title(f"{subj}: {grade}")
    st.caption(f"Student: {st.session_state.p_student} | Tutor: {st.session_state.p_tutor}")
    st.divider()

    if subj == "Mathematics":
        curr_set = content[st.session_state.set_idx]
        if st.session_state.phase == "familiarity":
            st.header(curr_set['topic'])
            c1, c2 = st.columns(2)
            if c1.button("Yes (Start)"): st.session_state.phase = "mastery"; st.rerun()
            if c2.button("No (Skip)"):
                record(subj, grade, curr_set['topic'], "Familiarity", "No")
                if st.session_state.bottleneck or st.session_state.set_idx == len(content)-1: st.session_state.step = "summary"
                else: st.session_state.set_idx += 1
                st.rerun()
        # ... (Rest of Math logic: Mastery/Subs)
        elif st.session_state.phase in ["mastery", "mastery_retry"]:
            st.subheader("Mastery Question")
            st.info(curr_set['mastery_q'])
            display_img(curr_set.get('image'))
            c1, c2 = st.columns(2)
            if c1.button("✅ Correct"):
                record(subj, grade, curr_set['topic'], "Mastery", "Correct")
                if st.session_state.set_idx < len(content)-1: st.session_state.set_idx += 1; st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
                st.rerun()
            if c2.button("❌ Incorrect"):
                record(subj, grade, curr_set['topic'], "Mastery", "Incorrect")
                st.session_state.phase = "subs"; st.session_state.sub_idx = 0; st.rerun()
        elif st.session_state.phase == "subs":
            sub = curr_set['subs'][st.session_state.sub_idx]
            st.write(f"Question: {sub['q']}")
            display_img(sub.get('image'))
            if st.button("Next"):
                if st.session_state.sub_idx < len(curr_set['subs'])-1: st.session_state.sub_idx += 1
                else: st.session_state.phase = "mastery_retry"
                st.rerun()

    elif subj == "English Language":
        # Sequential logic for English
        section = content[st.session_state.set_idx]
        st.header(section['section_title'])
        if section.get('content_text'): st.code(section['content_text'], language=None)
        q = section['questions'][st.session_state.sub_idx]
        st.subheader(f"Q: {q['q']}")
        if st.button("✅ Correct"):
            record(subj, grade, section['section_title'], q['q'], "Correct")
            if st.session_state.sub_idx < len(section['questions'])-1: st.session_state.sub_idx += 1
            elif st.session_state.set_idx < len(content)-1: st.session_state.set_idx += 1; st.session_state.sub_idx = 0
            else: st.session_state.step = "summary"
            st.rerun()
        if st.button("❌ Incorrect"):
            record(subj, grade, section['section_title'], q['q'], "Incorrect")
            st.session_state.step = "summary"; st.rerun()

# --- SUMMARY ---
elif st.session_state.step == "summary":
    st.header("Assessment Results")
    df = pd.DataFrame(st.session_state.results)
    st.table(df)
    obs = st.text_area("Final Observations")
    if st.button("Submit"):
        requests.post(WEBHOOK_URL, data=json.dumps({
            "tutor": st.session_state.p_tutor, "student": st.session_state.p_student,
            "subject": st.session_state.p_subject, "results": df.to_string(), "feedback": obs
        }))
        st.success("Submitted!")
