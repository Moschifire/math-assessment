import streamlit as st
import pandas as pd
import requests
import json
import os
from io import BytesIO

# --- CONFIG ---
# Replace with your actual Google Apps Script URL
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyZU-Km741xhQuKc9W98-xFGsaEQ18P2LgRKlCSNEKZDzYoXrqgpEA04WMoFLeq_WRpFQ/exec" 

st.set_page_config(page_title="Multi-Subject Diagnostic", layout="wide")

# --- DATA LOADER ---
@st.cache_data
def load_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f:
            return json.load(f)
    return {}

ALL_DATA = load_data()

# --- UNIVERSAL IMAGE LOADER ---
def display_img(url, w=450):
    if not url or not isinstance(url, str) or len(url) < 10: return
    try:
        f_url = url
        if 'drive.google.com' in url:
            f_id = url.split('/file/d/')[1].split('/')[0] if '/file/d/' in url else url.split('id=')[1].split('&')[0]
            f_url = f'https://drive.google.com/uc?export=download&id={f_id}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(f_url, headers=headers, timeout=10)
        if res.status_code == 200: st.image(BytesIO(res.content), width=w)
    except: pass

# --- STATE INITIALIZATION ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.results = []
    # Shared counters
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    # Math logic states
    st.session_state.phase = "familiarity"
    st.session_state.mastery_count = 0
    st.session_state.bottleneck = False

def record(subj, grade, topic, level, status):
    st.session_state.results.append({
        "Subject": subj, "Grade": grade, "Topic": topic, "Level": level, "Status": status
    })

def math_advance_logic():
    """Handles transitions for Math Scaffold logic."""
    content = ALL_DATA[st.session_state.p_subj][st.session_state.p_curr][st.session_state.p_grade]
    if st.session_state.set_idx < len(content) - 1:
        st.session_state.set_idx += 1
        st.session_state.sub_idx = 0
        st.session_state.phase = "familiarity"
        st.rerun()
    else:
        # Check for Grade Advance (if 100% Mastery achieved)
        if st.session_state.mastery_count >= len(content):
            grades = list(ALL_DATA[st.session_state.p_subj][st.session_state.p_curr].keys())
            g_idx = grades.index(st.session_state.p_grade)
            if g_idx < len(grades) - 1:
                st.session_state.p_grade = grades[g_idx + 1]
                st.session_state.set_idx = 0
                st.session_state.sub_idx = 0
                st.session_state.mastery_count = 0
                st.session_state.phase = "familiarity"
                st.session_state.bottleneck = True
                st.toast(f"Moving to {st.session_state.p_grade}!", icon="🚀")
                st.rerun()
        st.session_state.step = "summary"
        st.rerun()

# --- 1. SETUP SCREEN ---
if st.session_state.step == "setup":
    st.title("Diagnostic Assessment Setup")
    if not ALL_DATA:
        st.error("Missing content.json or invalid format.")
        st.stop()

    subjs = list(ALL_DATA.keys())
    s_subj = st.selectbox("Select Subject", subjs)

    currs = list(ALL_DATA[s_subj].keys()) if s_subj else []
    s_curr = st.selectbox("Select Curriculum", currs)

    grade_options = []
    if s_subj and s_curr:
        data_lvl2 = ALL_DATA[s_subj].get(s_curr, {})
        if isinstance(data_lvl2, dict):
            grade_options = list(data_lvl2.keys())
    
    s_grade = st.selectbox("Select Grade/Class", grade_options)
    t_tutor = st.text_input("Tutor Name")
    t_student = st.text_input("Student Name")

    if st.button("Begin Assessment"):
        if t_tutor and t_student and s_grade:
            st.session_state.update({
                "p_tutor": t_tutor, "p_student": t_student, "p_subj": s_subj,
                "p_curr": s_curr, "p_grade": s_grade, "step": "testing"
            })
            st.rerun()

# --- 2. TESTING SCREEN ---
elif st.session_state.step == "testing":
    subj, grade = st.session_state.p_subj, st.session_state.p_grade
    content = ALL_DATA[subj][st.session_state.p_curr][grade]
    
    st.title(f"{subj}: {grade}")
    st.caption(f"Tutor: {st.session_state.p_tutor} | Student: {st.session_state.p_student}")
    st.divider()

    # --- ENGINE: MATHEMATICS ---
    if subj == "Mathematics":
        curr_set = content[st.session_state.set_idx]
        
        if st.session_state.phase == "familiarity":
            st.header(curr_set['topic'])
            st.subheader("Is the student familiar with this?")
            c1, c2 = st.columns(2)
            if c1.button("Yes"): st.session_state.phase = "mastery"; st.rerun()
            if c2.button("No"):
                record(subj, grade, curr_set['topic'], "Familiarity", "Not Familiar")
                if st.session_state.bottleneck: st.session_state.step = "summary"; st.rerun()
                math_advance_logic()

        elif st.session_state.phase in ["mastery", "mastery_retry"]:
            lbl = "Mastery Question" if st.session_state.phase == "mastery" else "Mastery Question (Retry)"
            st.subheader(lbl)
            st.info(curr_set['mastery_q'])
            display_img(curr_set.get('image'))
            if st.checkbox("Show Hint"): st.warning(curr_set['mastery_hint'])
            
            c1, c2 = st.columns(2)
            if c1.button("✅ Correct"):
                record(subj, grade, curr_set['topic'], lbl, "Correct")
                st.session_state.mastery_count += 1
                math_advance_logic()
            if c2.button("❌ Incorrect"):
                record(subj, grade, curr_set['topic'], lbl, "Incorrect")
                if st.session_state.bottleneck or st.session_state.phase == "mastery_retry":
                    st.session_state.step = "summary"; st.rerun()
                else: st.session_state.phase = "subs"; st.session_state.sub_idx = 0; st.rerun()

        elif st.session_state.phase == "subs":
            sub = curr_set['subs'][st.session_state.sub_idx]
            st.subheader(f"Sub-Question {st.session_state.sub_idx + 1}")
            st.write(sub['q'])
            display_img(sub.get('image'))
            if st.checkbox("Show Sub-Hint"): st.warning(sub['h'])
            c1, c2 = st.columns(2)
            if c1.button("✅ Correct"):
                record(subj, grade, curr_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Correct")
                if st.session_state.sub_idx < len(curr_set['subs'])-1: st.session_state.sub_idx += 1; st.rerun()
                else: st.session_state.phase = "mastery_retry"; st.rerun()
            if c2.button("❌ Incorrect"):
                record(subj, grade, curr_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Incorrect")
                if st.session_state.bottleneck: st.session_state.step = "summary"; st.rerun()
                math_advance_logic()

    # --- ENGINE: ENGLISH LANGUAGE ---
    elif subj == "English Language":
        section = content[st.session_state.set_idx]
        st.header(section['section_title'])
        st.info(section['instruction'])
        if section.get('content_text'): st.code(section['content_text'], language=None)
        display_img(section.get('image'))
        
        q_list = section['questions']
        q = q_list[st.session_state.sub_idx]
        st.subheader(f"Question {st.session_state.sub_idx + 1}")
        st.write(q['q'])
        if st.checkbox("Show Hint"): st.warning(q['h'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record(subj, grade, section['section_title'], f"Q{st.session_state.sub_idx+1}", "Correct")
            if st.session_state.sub_idx < len(q_list)-1: st.session_state.sub_idx += 1
            elif st.session_state.set_idx < len(content)-1: st.session_state.set_idx += 1; st.session_state.sub_idx = 0
            else: st.session_state.step = "summary"
            st.rerun()
        if c2.button("❌ Incorrect"):
            record(subj, grade, section['section_title'], f"Q{st.session_state.sub_idx+1}", "Incorrect")
            st.session_state.step = "summary"; st.rerun()

# --- 3. SUMMARY SCREEN ---
elif st.session_state.step == "summary":
    st.header("Assessment Results")
    df = pd.DataFrame(st.session_state.results)
    st.table(df)
    obs = st.text_area("Tutor Observations")
    if st.button("Submit to Google Sheets"):
        payload = {
            "tutor": st.session_state.p_tutor, "student": st.session_state.p_student,
            "subject": st.session_state.p_subj, "grade": st.session_state.p_grade,
            "results": df.to_string(), "feedback": obs
        }
        try:
            requests.post(WEBHOOK_URL, data=json.dumps(payload))
            st.success("Submitted successfully!")
        except: st.error("Submission failed.")
    
    if st.button("New Assessment"):
        st.session_state.clear()
        st.rerun()
