import streamlit as st
import pandas as pd
import requests
import json
import os
import re
from io import BytesIO

# --- CONFIG ---
# PASTE YOUR GOOGLE APPS SCRIPT URL HERE
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxFm533cRPJWr3e-XBb0iHWoTJhKi0eERBGxXCJ_rkpMJP1fIyKPh4VmU2xE2F1aTr51g/exec" 

st.set_page_config(page_title="Math Diagnostic Assessment", layout="wide")

# --- HELPER: DIRECT IMAGE FETCHING ---
def display_google_drive_image(url, img_width=400):
    """Downloads image bytes from Google Drive and displays them in Streamlit."""
    if not url or not isinstance(url, str) or len(url) < 15:
        return
    
    file_id = None
    try:
        if '/file/d/' in url:
            file_id = url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in url:
            file_id = url.split('id=')[1].split('&')[0]
        
        if file_id:
            direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
            # Adding headers to mimic a browser browser to prevent Google from blocking the request
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(direct_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                st.image(BytesIO(response.content), width=img_width)
            else:
                st.error(f"Image Load Failed (Status {response.status_code}). Ensure the file is shared as 'Anyone with the link'.")
    except Exception as e:
        st.warning(f"Could not load image: {e}")

# --- DATA LOADER ---
def load_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f:
            return json.load(f)
    else:
        st.error("Missing 'content.json'.")
        return {}

ALL_CONTENT = load_data()

# --- INITIALIZE STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.p_tutor = ""
    st.session_state.p_student = ""
    st.session_state.p_curr = ""
    st.session_state.p_grade = ""
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    st.session_state.phase = "familiarity" 
    st.session_state.results = []
    st.session_state.mastery_count = 0
    st.session_state.bottleneck_active = False

def record_entry(topic, detail, status, hint_used):
    st.session_state.results.append({
        "Grade": st.session_state.p_grade,
        "Topic": topic,
        "Level": detail,
        "Status": status,
        "Hint": "Used" if hint_used else "None"
    })

def next_question_set():
    grade_data = ALL_CONTENT[st.session_state.p_curr][st.session_state.p_grade]
    if st.session_state.set_idx < len(grade_data) - 1:
        st.session_state.set_idx += 1
        st.session_state.sub_idx = 0
        st.session_state.phase = "familiarity"
    else:
        # Check if they mastered ALL 5 in the current grade
        if st.session_state.mastery_count >= len(grade_data):
            all_grades = list(ALL_CONTENT[st.session_state.p_curr].keys())
            g_idx = all_grades.index(st.session_state.p_grade)
            if g_idx < len(all_grades) - 1:
                st.session_state.p_grade = all_grades[g_idx + 1]
                st.session_state.set_idx = 0
                st.session_state.sub_idx = 0
                st.session_state.mastery_count = 0
                st.session_state.bottleneck_active = True
                st.session_state.phase = "familiarity"
            else: st.session_state.step = "summary"
        else: st.session_state.step = "summary"

# --- UI: SETUP ---
if st.session_state.step == "setup":
    st.title("Mathematics Diagnostic Setup")
    t_tutor = st.text_input("Tutor Name")
    t_student = st.text_input("Student Name")
    curriculums = list(ALL_CONTENT.keys()) if ALL_CONTENT else []
    t_curr = st.selectbox("Select Curriculum", curriculums) if curriculums else None
    if t_curr:
        grades = list(ALL_CONTENT[t_curr].keys())
        t_grade = st.selectbox("Select Starting Class", grades)
    
    if st.button("Begin Assessment"):
        if t_tutor and t_student:
            st.session_state.p_tutor = t_tutor
            st.session_state.p_student = t_student
            st.session_state.p_curr = t_curr
            st.session_state.p_grade = t_grade
            st.session_state.step = "testing"
            st.rerun()
        else: st.error("Please enter names.")

# --- UI: TESTING ---
elif st.session_state.step == "testing":
    grade_data = ALL_CONTENT[st.session_state.p_curr][st.session_state.p_grade]
    current_set = grade_data[st.session_state.set_idx]
    
    st.title(f"Diagnostic: {st.session_state.p_grade}")
    st.caption(f"Tutor: {st.session_state.p_tutor} | Student: {st.session_state.p_student}")
    st.divider()

    if st.session_state.phase == "familiarity":
        st.header(current_set['topic'])
        st.subheader("Is the student familiar with this topic?")
        c1, c2 = st.columns(2)
        if c1.button("Yes"):
            st.session_state.phase = "mastery"
            st.rerun()
        if c2.button("No"):
            record_entry(current_set['topic'], "Familiarity Check", "Not Familiar", False)
            if st.session_state.bottleneck_active: st.session_state.step = "summary"
            else: next_question_set()
            st.rerun()

    elif st.session_state.phase in ["mastery", "mastery_retry"]:
        label = "Mastery Question" if st.session_state.phase == "mastery" else "Mastery Question (Retry)"
        st.subheader(label)
        st.info(current_set['mastery_q'])
        
        # FIX: Check for both possible JSON key names for the mastery image
        m_img = current_set.get('image') or current_set.get('mastery_image')
        display_google_drive_image(m_img, img_width=500)
        
        h_used = st.checkbox("Show Hint?")
        if h_used: st.warning(current_set['mastery_hint'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(current_set['topic'], label, "Correct", h_used)
            st.session_state.mastery_count += 1
            next_question_set()
            st.rerun()
        if c2.button("❌ Incorrect"):
            record_entry(current_set['topic'], label, "Incorrect", h_used)
            if st.session_state.phase == "mastery_retry" or st.session_state.bottleneck_active:
                st.session_state.step = "summary"
            else:
                st.session_state.phase = "subs"
                st.session_state.sub_idx = 0
            st.rerun()

    elif st.session_state.phase == "subs":
        sub = current_set['subs'][st.session_state.sub_idx]
        st.subheader(f"Sub-Question {st.session_state.sub_idx + 1}")
        st.write(sub['q'])
        
        display_google_drive_image(sub.get('image'), img_width=400)
        
        h_used = st.checkbox(f"Show hint?")
        if h_used: st.warning(sub['h'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Correct", h_used)
            if st.session_state.sub_idx < len(current_set['subs']) - 1:
                st.session_state.sub_idx += 1
            else:
                st.session_state.phase = "mastery_retry"
            st.rerun()
        if c2.button("❌ Incorrect"):
            record_entry(current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Incorrect", h_used)
            # LOGIC: Move to next set immediately on sub-question failure
            next_question_set()
            st.rerun()

elif st.session_state.step == "summary":
    st.header("Assessment Summary")
    st.table(pd.DataFrame(st.session_state.results))
    report_body = "\n".join([f"[{r['Grade']}] {r['Topic']} | {r['Level']}: {r['Status']}" for r in st.session_state.results])
    
    if st.button("Final Submit to Google Sheets"):
        try:
            payload = {
                "tutor": st.session_state.p_tutor, 
                "student": st.session_state.p_student, 
                "results": report_body,
                "curriculum": st.session_state.p_curr,
                "grade": st.session_state.p_grade
            }
            requests.post(WEBHOOK_URL, data=json.dumps(payload))
            st.success("Successfully Submitted!")
        except: st.error("Submission failed.")
