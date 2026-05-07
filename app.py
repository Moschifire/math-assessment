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
    # Math States
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    st.session_state.phase = "familiarity"
    st.session_state.mastery_count = 0
    st.session_state.bottleneck = False
    # English States
    st.session_state.eng_section_idx = 0
    st.session_state.eng_q_idx = 0

def record(subj, grade, topic, q, status):
    st.session_state.results.append({"Subject": subj, "Grade": grade, "Topic": topic, "Question": q, "Status": status})

# --- SETUP SCREEN ---
if st.session_state.step == "setup":
    st.title("Diagnostic Assessment Setup")
    st.session_state.p_tutor = st.text_input("Tutor Name")
    st.session_state.p_student = st.text_input("Student Name")
    st.session_state.p_subject = st.selectbox("Subject", list(ALL_DATA.keys()))
    
    if st.session_state.p_subject:
        subj_data = ALL_DATA[st.session_state.p_subject]
        st.session_state.p_curr = st.selectbox("Curriculum", list(subj_data.keys()))
        if st.session_state.p_curr:
            st.session_state.p_grade = st.selectbox("Grade", list(subj_data[st.session_state.p_curr].keys()))
            
    if st.button("Start Assessment"):
        if st.session_state.p_tutor and st.session_state.p_student:
            st.session_state.step = "testing"
            st.rerun()

# --- TESTING SCREEN ---
elif st.session_state.step == "testing":
    subj = st.session_state.p_subject
    grade_content = ALL_DATA[subj][st.session_state.p_curr][st.session_state.p_grade]
    
    st.title(f"{subj} Diagnostic: {st.session_state.p_grade}")
    st.caption(f"Tutor: {st.session_state.p_tutor} | Student: {st.session_state.p_student}")
    st.divider()

    # --- MATH LOGIC (Mastery/Subs) ---
    if subj == "Mathematics":
        curr_set = grade_content[st.session_state.set_idx]
        
        if st.session_state.phase == "familiarity":
            st.header(curr_set['topic'])
            if st.button("Familiar (Start Mastery)"): st.session_state.phase = "mastery"; st.rerun()
            if st.button("Not Familiar (Skip Set)"):
                record(subj, st.session_state.p_grade, curr_set['topic'], "Familiarity", "No")
                if st.session_state.bottleneck or st.session_state.set_idx == len(grade_content)-1:
                    st.session_state.step = "summary"
                else: st.session_state.set_idx += 1
                st.rerun()

        elif st.session_state.phase in ["mastery", "mastery_retry"]:
            st.subheader("Mastery Question")
            st.info(curr_set['mastery_q'])
            display_img(curr_set.get('image'))
            c1, c2 = st.columns(2)
            if c1.button("✅ Correct"):
                record(subj, st.session_state.p_grade, curr_set['topic'], "Mastery", "Correct")
                st.session_state.mastery_count += 1
                if st.session_state.set_idx < len(grade_content)-1:
                    st.session_state.set_idx += 1; st.session_state.phase = "familiarity"
                elif st.session_state.mastery_count == len(grade_content):
                    # Advance grade logic... (simpler version for brevity)
                    st.session_state.step = "summary"
                else: st.session_state.step = "summary"
                st.rerun()
            if c2.button("❌ Incorrect"):
                record(subj, st.session_state.p_grade, curr_set['topic'], "Mastery", "Incorrect")
                if st.session_state.bottleneck: st.session_state.step = "summary"
                else: st.session_state.phase = "subs"; st.session_state.sub_idx = 0
                st.rerun()

        elif st.session_state.phase == "subs":
            sub = curr_set['subs'][st.session_state.sub_idx]
            st.write(f"Sub-Question {st.session_state.sub_idx+1}: {sub['q']}")
            display_img(sub.get('image'))
            c1, c2 = st.columns(2)
            if c1.button("✅ Correct"):
                if st.session_state.sub_idx < len(curr_set['subs'])-1: st.session_state.sub_idx += 1
                else: st.session_state.phase = "mastery_retry"
                st.rerun()
            if c2.button("❌ Incorrect"):
                if st.session_state.set_idx < len(grade_content)-1: 
                    st.session_state.set_idx += 1; st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
                st.rerun()

    # --- ENGLISH LOGIC (Sequential/Linear) ---
    elif subj == "English Language":
        section = grade_content[st.session_state.eng_section_idx]
        st.header(section['section_title'])
        st.markdown(f"**Instruction:** {section['instruction']}")
        
        # Display large text block for reading
        if section.get('content_text'):
            st.subheader("Reading Material:")
            st.code(section['content_text'], language=None)
        
        display_img(section.get('image'))
        st.divider()
        
        # Display current question in section
        q_data = section['questions'][st.session_state.eng_q_idx]
        st.subheader(f"Question {st.session_state.eng_q_idx + 1}")
        st.write(q_data['q'])
        if st.checkbox("Show Hint"): st.info(q_data['h'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record(subj, st.session_state.p_grade, section['section_title'], q_data['q'], "Correct")
            # Move to next question or next section
            if st.session_state.eng_q_idx < len(section['questions']) - 1:
                st.session_state.eng_q_idx += 1
            elif st.session_state.eng_section_idx < len(grade_content) - 1:
                st.session_state.eng_section_idx += 1
                st.session_state.eng_q_idx = 0
            else: st.session_state.step = "summary"
            st.rerun()
            
        if c2.button("❌ Incorrect"):
            record(subj, st.session_state.p_grade, section['section_title'], q_data['q'], "Incorrect")
            # In English, if they fail, we typically end that section or end assessment
            st.session_state.step = "summary"
            st.rerun()

# --- SUMMARY ---
elif st.session_state.step == "summary":
    st.title("Assessment Results")
    df = pd.DataFrame(st.session_state.results)
    st.table(df)
    obs = st.text_area("Final Observations")
    if st.button("Submit"):
        requests.post(WEBHOOK_URL, data=json.dumps({
            "tutor": st.session_state.p_tutor,
            "student": st.session_state.p_student,
            "subject": st.session_state.p_subject,
            "results": df.to_string(),
            "feedback": obs
        }))
        st.success("Submitted!")
