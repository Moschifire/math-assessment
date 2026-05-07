import streamlit as st
import pandas as pd
import requests
import json
import os
from io import BytesIO

# --- CONFIG ---
# PASTE YOUR GOOGLE APPS SCRIPT URL HERE
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyZU-Km741xhQuKc9W98-xFGsaEQ18P2LgRKlCSNEKZDzYoXrqgpEA04WMoFLeq_WRpFQ/exec" 

st.set_page_config(page_title="Multi-Subject Diagnostic Pro", layout="wide")

# --- DATA LOADER ---
def load_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f:
            return json.load(f)
    return {}

ALL_DATA = load_data()

# --- UNIVERSAL IMAGE LOADER (Craft.do & GDrive optimized) ---
def display_img(url, w=450):
    if not url or not isinstance(url, str) or len(url) < 10: return
    try:
        f_url = url
        # Google Drive Conversion
        if 'drive.google.com' in url:
            f_id = url.split('/file/d/')[1].split('/')[0] if '/file/d/' in url else url.split('id=')[1].split('&')[0]
            f_url = f'https://drive.google.com/uc?export=download&id={f_id}'
        
        # Request with specific headers for Craft.do and GDrive
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        res = requests.get(f_url, headers=headers, timeout=12)
        if res.status_code == 200:
            st.image(BytesIO(res.content), width=w)
    except:
        pass

# --- STATE MGMT ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.results = []
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    st.session_state.phase = "familiarity"
    st.session_state.mastery_count = 0
    st.session_state.perfect_score = True 
    st.session_state.bottleneck_active = False 

def record(subj, grade, topic, level, status):
    st.session_state.results.append({
        "Subject": subj, "Grade": grade, "Topic": topic, "Level": level, "Status": status
    })

def advance_logic():
    subj = st.session_state.p_subject
    curr_data = ALL_DATA[subj][st.session_state.p_curr][st.session_state.p_grade]
    all_grades = list(ALL_DATA[subj][st.session_state.p_curr].keys())
    g_idx = all_grades.index(st.session_state.p_grade)

    if subj == "Mathematics":
        if st.session_state.set_idx < len(curr_data) - 1:
            st.session_state.set_idx += 1
            st.session_state.sub_idx = 0
            st.session_state.phase = "familiarity"
        else:
            # Must have 100% Mastery correct to level up
            if st.session_state.mastery_count >= len(curr_data) and g_idx < len(all_grades) - 1:
                st.session_state.p_grade = all_grades[g_idx + 1]
                st.session_state.set_idx = 0
                st.session_state.sub_idx = 0
                st.session_state.mastery_count = 0
                st.session_state.phase = "familiarity"
                st.session_state.bottleneck_active = True
                st.toast(f"Moving to {st.session_state.p_grade}", icon="🚀")
            else: st.session_state.step = "summary"
    
    else: # ENGLISH LOGIC
        section = curr_data[st.session_state.set_idx]
        # 1. Move to next question in current section
        if st.session_state.sub_idx < len(section['questions']) - 1:
            st.session_state.sub_idx += 1
        # 2. Move to next section in current grade
        elif st.session_state.set_idx < len(curr_data) - 1:
            st.session_state.set_idx += 1
            st.session_state.sub_idx = 0
            st.session_state.phase = "familiarity"
        # 3. End of Grade Reach
        else:
            if st.session_state.perfect_score and g_idx < len(all_grades) - 1:
                st.session_state.p_grade = all_grades[g_idx + 1]
                st.session_state.set_idx = 0
                st.session_state.sub_idx = 0
                st.session_state.phase = "familiarity"
                st.session_state.bottleneck_active = True
                st.toast(f"Level Up: {st.session_state.p_grade}", icon="📚")
            else: st.session_state.step = "summary"
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
            s_grade = st.selectbox("Select Starting Grade", grades)
            
    t_tutor = st.text_input("Tutor Name")
    t_student = st.text_input("Student Name")

    if st.button("Begin Assessment"):
        if t_tutor and t_student and s_grade:
            st.session_state.update({
                "p_tutor": t_tutor, "p_student": t_student, "p_subject": s_subj,
                "p_curr": s_curr, "p_grade": s_grade, "p_start_grade": s_grade,
                "step": "testing", "perfect_score": True
            })
            st.rerun()

# --- 2. TESTING ---
elif st.session_state.step == "testing":
    subj, grade = st.session_state.p_subject, st.session_state.p_grade
    content = ALL_DATA[subj][st.session_state.p_curr][grade]
    current_set = content[st.session_state.set_idx]
    
    st.title(f"{subj}: {grade}")
    st.caption(f"Tutor: {st.session_state.p_tutor} | Student: {st.session_state.p_student}")
    st.divider()

    # --- SHARED PHASE: FAMILIARITY CHECK ---
    if st.session_state.phase == "familiarity":
        topic_label = current_set.get('topic') or current_set.get('section_title')
        st.header(topic_label)
        st.subheader("Is the student familiar with this topic?")
        
        c1, c2 = st.columns([1, 5])
        if c1.button("Yes"): 
            st.session_state.phase = "content"
            st.rerun()
        if c2.button("No"):
            record(subj, grade, topic_label, "Familiarity", "No")
            st.session_state.perfect_score = False
            if st.session_state.bottleneck_active: st.session_state.step = "summary"
            else: advance_logic()
            st.rerun()

    # --- PHASE: CONTENT ---
    elif st.session_state.phase in ["content", "mastery_retry", "subs"]:
        
        if subj == "Mathematics":
            # --- MATH LOGIC ---
            if st.session_state.phase in ["content", "mastery_retry"]:
                lbl = "Mastery Question" if st.session_state.phase == "content" else "Mastery Question (Retry)"
                st.subheader(lbl)
                st.info(current_set['mastery_q'])
                # FIXED: Check both image keys during Retry as well
                m_img = current_set.get('image') or current_set.get('mastery_image')
                display_img(m_img, w=500)
                
                if st.checkbox("Show Hint"): st.warning(current_set['mastery_hint'])
                
                c1, c2 = st.columns(2)
                if c1.button("✅ Correct"):
                    record(subj, grade, current_set['topic'], lbl, "Correct")
                    st.session_state.mastery_count += 1
                    advance_logic()
                if c2.button("❌ Incorrect"):
                    record(subj, grade, current_set['topic'], lbl, "Incorrect")
                    st.session_state.perfect_score = False
                    if st.session_state.bottleneck_active or st.session_state.phase == "mastery_retry":
                        st.session_state.step = "summary"
                    else:
                        st.session_state.phase = "subs"; st.session_state.sub_idx = 0
                    st.rerun()

            elif st.session_state.phase == "subs":
                sub = current_set['subs'][st.session_state.sub_idx]
                st.subheader(f"Sub-Question {st.session_state.sub_idx+1}")
                st.write(sub['q'])
                display_img(sub.get('image'))
                c1, c2 = st.columns(2)
                if c1.button("✅ Correct"):
                    record(subj, grade, current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Correct")
                    if st.session_state.sub_idx < len(current_set['subs'])-1: st.session_state.sub_idx += 1; st.rerun()
                    else: st.session_state.phase = "mastery_retry"; st.rerun()
                if c2.button("❌ Incorrect"):
                    record(subj, grade, current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Incorrect")
                    st.session_state.perfect_score = False
                    if st.session_state.bottleneck_active: st.session_state.step = "summary"
                    else: advance_logic()
                    st.rerun()

        else: # --- ENGINE: ENGLISH LANGUAGE ---
            st.header(current_set['section_title'])
            st.info(f"**Instruction:** {current_set['instruction']}")
            if current_set.get('content_text'): st.code(current_set['content_text'], language=None)
            
            # Display Section Image
            display_img(current_set.get('image') or current_set.get('mastery_image'), w=500)
            
            q_list = current_set['questions']
            q = q_list[st.session_state.sub_idx]
            st.divider()
            st.subheader(f"Question {st.session_state.sub_idx + 1}")
            st.write(q['q'])
            
            # FIXED: Display Question-level Image if exists
            if q.get('image'): display_img(q.get('image'), w=400)
            
            if st.checkbox("Show Hint"): st.warning(q['h'])
            
            c1, c2 = st.columns(2)
            if c1.button("✅ Correct"):
                record(subj, grade, current_set['section_title'], f"Q{st.session_state.sub_idx+1}", "Correct")
                advance_logic()
            if c2.button("❌ Incorrect"):
                record(subj, grade, current_set['section_title'], f"Q{st.session_state.sub_idx+1}", "Incorrect")
                st.session_state.perfect_score = False
                # BOTTLENECK RULE: End if in higher class. Else, keep asking questions in section.
                if st.session_state.bottleneck_active: st.session_state.step = "summary"
                else: advance_logic()
                st.rerun()

# --- 3. SUMMARY ---
elif st.session_state.step == "summary":
    st.header("Assessment Summary")
    df = pd.DataFrame(st.session_state.results)
    st.table(df)
    obs = st.text_area("Tutor Observations")
    if st.button("Final Submit"):
        payload = {
            "tutor": st.session_state.p_tutor, "student": st.session_state.p_student,
            "subject": st.session_state.p_subject, "curriculum": st.session_state.p_curr,
            "grade": st.session_state.p_grade, "results": df.to_string(), "feedback": obs
        }
        try:
            requests.post(WEBHOOK_URL, data=json.dumps(payload))
            st.success("Results submitted successfully!")
        except: st.error("Submission failed.")
    if st.button("New Assessment"):
        st.session_state.clear(); st.rerun()
