import streamlit as st
import pandas as pd
import requests
import json
import os
import re

# --- CONFIG ---
# PASTE YOUR GOOGLE APPS SCRIPT URL HERE
WEBHOOK_URL = "https://script.google.com/macros/s/XXXX/exec" 

st.set_page_config(page_title="Math Diagnostic Assessment", layout="wide")

# --- HELPER: ROBUST GOOGLE DRIVE IMAGE CONVERTER ---
def get_google_drive_direct_url(url):
    """Converts various Google Drive link formats into direct image embed links."""
    if not url or not isinstance(url, str) or 'drive.google.com' not in url:
        return None
    
    try:
        # Extract ID from /file/d/[ID]/view
        file_id_match = re.search(r'/file/d/([0-9a-zA-Z_-]+)', url)
        if file_id_match:
            return f'https://drive.google.com/uc?export=view&id={file_id_match.group(1)}'
        
        # Extract ID from ?id=[ID]
        id_match = re.search(r'id=([0-9a-zA-Z_-]+)', url)
        if id_match:
            return f'https://drive.google.com/uc?export=view&id={id_match.group(1)}'
            
        return url
    except Exception:
        return None

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

# --- UI: SETUP ---
if st.session_state.step == "setup":
    st.title("Mathematics Diagnostic Setup")
    t_tutor = st.text_input("Tutor Name")
    t_student = st.text_input("Student Name")
    
    curriculums = list(ALL_CONTENT.keys())
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
        else:
            st.error("Please enter both names.")

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
        if c1.button("Yes, proceed"):
            st.session_state.phase = "mastery"
            st.rerun()
        if c2.button("No, skip topic"):
            record_entry(current_set['topic'], "Familiarity Check", "Not Familiar", False)
            if st.session_state.bottleneck_active:
                st.session_state.step = "summary"
            else:
                if st.session_state.set_idx < len(grade_data) - 1:
                    st.session_state.set_idx += 1
                else: st.session_state.step = "summary"
            st.rerun()

    elif st.session_state.phase == "mastery":
        st.subheader("Mastery Level Question")
        st.info(current_set['mastery_q'])
        
        # Display Image with Safety Check
        img_url = get_google_drive_direct_url(current_set.get('image'))
        if img_url:
            st.image(img_url, use_container_width=True)
            
        h_used = st.checkbox("Show Hint to student?")
        if h_used: st.warning(current_set['mastery_hint'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(current_set['topic'], "Mastery Q", "Correct", h_used)
            st.session_state.mastery_count += 1
            if st.session_state.set_idx < len(grade_data) - 1:
                st.session_state.set_idx += 1
                st.session_state.phase = "familiarity"
            else:
                # Grade Advance Check
                if st.session_state.mastery_count == len(grade_data):
                    all_grades = list(ALL_CONTENT[st.session_state.p_curr].keys())
                    g_idx = all_grades.index(st.session_state.p_grade)
                    if g_idx < len(all_grades) - 1:
                        st.session_state.p_grade = all_grades[g_idx + 1]
                        st.session_state.set_idx = 0
                        st.session_state.mastery_count = 0
                        st.session_state.bottleneck_active = True
                        st.session_state.phase = "familiarity"
                        st.success(f"Advancing to {st.session_state.p_grade}!")
                    else: st.session_state.step = "summary"
                else: st.session_state.step = "summary"
            st.rerun()
            
        if c2.button("❌ Incorrect"):
            record_entry(current_set['topic'], "Mastery Q", "Incorrect", h_used)
            if st.session_state.bottleneck_active:
                st.session_state.step = "summary"
            else:
                st.session_state.phase = "subs"
                st.session_state.sub_idx = 0
            st.rerun()

    elif st.session_state.phase == "subs":
        sub = current_set['subs'][st.session_state.sub_idx]
        st.subheader(f"Diving Deeper: Sub-Question {st.session_state.sub_idx + 1}")
        st.write(sub['q'])
        
        # Display Image with Safety Check
        img_url_sub = get_google_drive_direct_url(sub.get('image'))
        if img_url_sub:
            st.image(img_url_sub, use_container_width=True)
            
        h_used = st.checkbox(f"Show hint for sub-question?")
        if h_used: st.warning(sub['h'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Next/Correct"):
            record_entry(current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Correct", h_used)
            if st.session_state.sub_idx < len(current_set['subs']) - 1:
                st.session_state.sub_idx += 1
            else:
                if st.session_state.set_idx < len(grade_data) - 1:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()
        if c2.button("❌ Incorrect"):
            record_entry(current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Incorrect", h_used)
            if st.session_state.sub_idx < len(current_set['subs']) - 1:
                st.session_state.sub_idx += 1
            else:
                if st.session_state.set_idx < len(grade_data) - 1:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()

elif st.session_state.step == "summary":
    st.header("Assessment Summary")
    st.table(pd.DataFrame(st.session_state.results))
    
    report_body = ""
    for r in st.session_state.results:
        report_body += f"[{r['Grade']}] {r['Topic']} | {r['Level']}: {r['Status']} (Hint: {r['Hint']})\n"

    if st.button("Final Submit to Google Sheets"):
        payload = {
            "tutor": st.session_state.p_tutor,
            "student": st.session_state.p_student,
            "curriculum": st.session_state.p_curr,
            "grade": st.session_state.p_grade,
            "results": report_body
        }
        try:
            requests.post(WEBHOOK_URL, data=json.dumps(payload))
            st.success("Results submitted!")
        except: st.error("Failed to submit.")
