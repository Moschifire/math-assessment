import streamlit as st
import pandas as pd
import requests
import json
import os
from io import BytesIO

# --- CONFIG ---
# PASTE YOUR GOOGLE APPS SCRIPT URL HERE
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyZU-Km741xhQuKc9W98-xFGsaEQ18P2LgRKlCSNEKZDzYoXrqgpEA04WMoFLeq_WRpFQ/exec" 

st.set_page_config(page_title="Math & English Diagnostic Pro", layout="wide")

# --- DATA LOADER ---
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

# --- STATE MGMT ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.results = []
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    st.session_state.phase = "familiarity"
    st.session_state.mastery_count = 0
    st.session_state.bottleneck_active = False # Only True if current_grade > start_grade

def record(subj, grade, topic, level, status):
    st.session_state.results.append({
        "Subject": subj, "Grade": grade, "Topic": topic, "Level": level, "Status": status
    })

def advance_logic():
    """Unified logic to handle transitions while respecting the Start Grade bottleneck."""
    subj = st.session_state.p_subject
    curr_data = ALL_DATA[subj][st.session_state.p_curr][st.session_state.p_grade]
    all_grades = list(ALL_DATA[subj][st.session_state.p_curr].keys())
    g_idx = all_grades.index(st.session_state.p_grade)

    if subj == "Mathematics":
        # Move to next question set in current grade
        if st.session_state.set_idx < len(curr_data) - 1:
            st.session_state.set_idx += 1
            st.session_state.sub_idx = 0
            st.session_state.phase = "familiarity"
        else:
            # End of Grade Reach: Check for Perfect Mastery to Advance
            if st.session_state.mastery_count >= len(curr_data) and g_idx < len(all_grades) - 1:
                st.session_state.p_grade = all_grades[g_idx + 1]
                st.session_state.set_idx = 0
                st.session_state.sub_idx = 0
                st.session_state.mastery_count = 0
                st.session_state.phase = "familiarity"
                st.session_state.bottleneck_active = True # Crossing into higher grade
                st.toast(f"Level Up! Moving to {st.session_state.p_grade}", icon="🚀")
            else:
                st.session_state.step = "summary"
    
    else: # ENGINE: ENGLISH LANGUAGE
        section = curr_data[st.session_state.set_idx]
        if st.session_state.sub_idx < len(section['questions']) - 1:
            st.session_state.sub_idx += 1
        elif st.session_state.set_idx < len(curr_data) - 1:
            st.session_state.set_idx += 1
            st.session_state.sub_idx = 0
        else:
            # English Grade Transition (if all previous were correct)
            if g_idx < len(all_grades) - 1:
                st.session_state.p_grade = all_grades[g_idx + 1]
                st.session_state.set_idx = 0
                st.session_state.sub_idx = 0
                st.session_state.bottleneck_active = True # Crossing into higher grade
                st.toast(f"Level Up! Moving to {st.session_state.p_grade}", icon="📚")
            else:
                st.session_state.step = "summary"
    st.rerun()

# --- 1. SETUP ---
if st.session_state.step == "setup":
    st.title("Diagnostic Assessment Setup")
    subjs = list(ALL_DATA.keys())
    s_subj = st.selectbox("Select Subject", subjs) if subjs else None
    
    if s_subj:
        currs = list(ALL_DATA[s_subj].keys())
        s_curr = st.selectbox("Select Curriculum", currs)
        if s_curr:
            grades = list(ALL_DATA[s_subj][s_curr].keys())
            s_grade = st.selectbox("Select Starting Class", grades)
            
    t_tutor = st.text_input("Tutor Name")
    t_student = st.text_input("Student Name")

    if st.button("Begin Assessment"):
        if t_tutor and t_student and s_grade:
            st.session_state.update({
                "p_tutor": t_tutor, "p_student": t_student, "p_subject": s_subj,
                "p_curr": s_curr, "p_grade": s_grade, "p_start_grade": s_grade,
                "step": "testing"
            })
            st.rerun()

# --- 2. TESTING ---
elif st.session_state.step == "testing":
    subj, grade = st.session_state.p_subject, st.session_state.p_grade
    content = ALL_DATA[subj][st.session_state.p_curr][grade]
    
    st.title(f"{subj}: {grade}")
    st.caption(f"Tutor: {st.session_state.p_tutor} | Student: {st.session_state.p_student} | (Starting Class: {st.session_state.p_start_grade})")
    st.divider()

    if subj == "Mathematics":
        curr_set = content[st.session_state.set_idx]
        if st.session_state.phase == "familiarity":
            st.header(curr_set['topic'])
            c1, c2 = st.columns(2)
            if c1.button("Yes"): st.session_state.phase = "mastery"; st.rerun()
            if c2.button("No"):
                record(subj, grade, curr_set['topic'], "Familiarity", "No")
                if st.session_state.bottleneck_active: st.session_state.step = "summary"; st.rerun()
                else: advance_logic()

        elif st.session_state.phase in ["mastery", "mastery_retry"]:
            lbl = "Mastery Question" if st.session_state.phase == "mastery" else "Mastery Question (Retry)"
            st.subheader(lbl)
            st.info(curr_set['mastery_q'])
            display_img(curr_set.get('image') or curr_set.get('mastery_image'))
            if st.checkbox("Show Hint"): st.warning(curr_set['mastery_hint'])
            c1, c2 = st.columns(2)
            if c1.button("✅ Correct"):
                record(subj, grade, curr_set['topic'], lbl, "Correct")
                st.session_state.mastery_count += 1
                advance_logic()
            if c2.button("❌ Incorrect"):
                record(subj, grade, curr_set['topic'], lbl, "Incorrect")
                if st.session_state.bottleneck_active or st.session_state.phase == "mastery_retry":
                    st.session_state.step = "summary"; st.rerun()
                else: st.session_state.phase = "subs"; st.session_state.sub_idx = 0; st.rerun()

        elif st.session_state.phase == "subs":
            sub = curr_set['subs'][st.session_state.sub_idx]
            st.subheader(f"Sub-Question {st.session_state.sub_idx+1}")
            st.write(sub['q'])
            display_img(sub.get('image'))
            c1, c2 = st.columns(2)
            if c1.button("✅ Correct"):
                record(subj, grade, curr_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Correct")
                if st.session_state.sub_idx < len(curr_set['subs'])-1: st.session_state.sub_idx += 1; st.rerun()
                else: st.session_state.phase = "mastery_retry"; st.rerun()
            if c2.button("❌ Incorrect"):
                record(subj, grade, curr_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Incorrect")
                if st.session_state.bottleneck_active: st.session_state.step = "summary"
                else: advance_logic()
                st.rerun()

    else: # ENGINE: ENGLISH LANGUAGE
        section = content[st.session_state.set_idx]
        st.header(section['section_title'])
        st.info(section['instruction'])
        if section.get('content_text'): st.code(section['content_text'], language=None)
        display_img(section.get('image') or section.get('mastery_image'))
        
        q_list = section['questions']
        q = q_list[st.session_state.sub_idx]
        st.subheader(f"Question {st.session_state.sub_idx + 1}")
        st.write(q['q'])
        if st.checkbox("Show Hint"): st.warning(q['h'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record(subj, grade, section['section_title'], f"Q{st.session_state.sub_idx+1}", "Correct")
            advance_logic()
        if c2.button("❌ Incorrect"):
            record(subj, grade, section['section_title'], f"Q{st.session_state.sub_idx+1}", "Incorrect")
            if st.session_state.bottleneck_active: st.session_state.step = "summary"
            else: advance_logic() # English allows finishing set in start_grade even if incorrect
            st.rerun()

# --- 3. SUMMARY ---
elif st.session_state.step == "summary":
    st.header("Assessment Results")
    df = pd.DataFrame(st.session_state.results)
    st.table(df)
    obs = st.text_area("Tutor Observations")
    if st.button("Final Submit"):
        payload = {
            "tutor": st.session_state.p_tutor, 
            "student": st.session_state.p_student,
            "subject": st.session_state.p_subject, 
            "curriculum": st.session_state.p_curr,
            "grade": st.session_state.p_grade,
            "results": df.to_string(), 
            "feedback": obs
        }
        try:
            requests.post(WEBHOOK_URL, data=json.dumps(payload))
            st.success("Submitted successfully!")
        except: st.error("Submission failed.")
    if st.button("New Assessment"):
        st.session_state.clear()
        st.rerun()
