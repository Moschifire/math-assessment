import streamlit as st
import pandas as pd
import requests
import json
import os

# --- CONFIG ---
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxFm533cRPJWr3e-XBb0iHWoTJhKi0eERBGxXCJ_rkpMJP1fIyKPh4VmU2xE2F1aTr51g/exec" 

st.set_page_config(page_title="Dynamic Math Diagnostic", layout="wide")

# --- DATA LOADER ---
def load_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f:
            return json.load(f)
    else:
        st.error("Data file 'content.json' not found!")
        return {}

ALL_CONTENT = load_data()

# --- INITIALIZE STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.p_curr = ""
    st.session_state.p_grade = ""
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    st.session_state.phase = "familiarity"
    st.session_state.results = []
    st.session_state.bottleneck = False

# --- UI: SETUP ---
if st.session_state.step == "setup":
    st.title("Math Assessment Setup")
    
    t_tutor = st.text_input("Tutor Name")
    t_student = st.text_input("Student Name")
    
    # Dynamic Dropdowns based on JSON file
    t_curr = st.selectbox("Select Curriculum", list(ALL_CONTENT.keys()))
    
    if t_curr:
        t_grade = st.selectbox("Select Class", list(ALL_CONTENT[t_curr].keys()))
    
    if st.button("Begin Assessment"):
        if t_tutor and t_student:
            st.session_state.p_tutor = t_tutor
            st.session_state.p_student = t_student
            st.session_state.p_curr = t_curr
            st.session_state.p_grade = t_grade
            st.session_state.step = "testing"
            st.rerun()

# --- UI: TESTING ---
elif st.session_state.step == "testing":
    # Filter content by selection
    grade_data = ALL_CONTENT[st.session_state.p_curr][st.session_state.p_grade]
    current_set = grade_data[st.session_state.set_idx]
    
    st.title(f"{st.session_state.p_curr}: {st.session_state.p_grade}")
    st.write(f"**Tutor:** {st.session_state.p_tutor} | **Student:** {st.session_state.p_student}")

    if st.session_state.phase == "familiarity":
        st.subheader(current_set['topic'])
        st.write("Is the student familiar with this topic?")
        c1, c2 = st.columns(2)
        if c1.button("Yes"):
            st.session_state.phase = "mastery"
            st.rerun()
        if c2.button("No, skip"):
            st.session_state.results.append({"Topic": current_set['topic'], "Status": "Not Familiar"})
            st.session_state.bottleneck = True
            if st.session_state.set_idx < len(grade_data) - 1:
                st.session_state.set_idx += 1
            else: st.session_state.step = "summary"
            st.rerun()

    elif st.session_state.phase == "mastery":
        st.subheader("Mastery Question")
        st.info(current_set['mastery_q'])
        
        # IMAGE SUPPORT
        if current_set.get('mastery_image'):
            st.image(current_set['mastery_image'], width=400)
            
        if st.checkbox("Show Hint"):
            st.warning(current_set['mastery_hint'])
            
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            st.session_state.results.append({"Topic": current_set['topic'], "Status": "Mastered"})
            if st.session_state.set_idx < len(grade_data) - 1:
                st.session_state.set_idx += 1
                st.session_state.phase = "familiarity"
            else:
                st.session_state.step = "summary"
            st.rerun()
        if c2.button("❌ Incorrect"):
            st.session_state.phase = "subs"
            st.rerun()

    elif st.session_state.phase == "subs":
        sub = current_set['subs'][st.session_state.sub_idx]
        st.subheader(f"Sub-Question {st.session_state.sub_idx + 1}")
        st.write(sub['q'])
        
        if sub.get('image'):
            st.image(sub['image'], width=300)
            
        if st.checkbox("Show Sub-Hint"):
            st.warning(sub['h'])
            
        if st.button("Next Sub-Question"):
            if st.session_state.sub_idx < len(current_set['subs']) - 1:
                st.session_state.sub_idx += 1
            else:
                st.session_state.sub_idx = 0
                if st.session_state.set_idx < len(grade_data) - 1:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()

# --- UI: SUMMARY ---
elif st.session_state.step == "summary":
    st.header("Assessment Finished")
    st.table(st.session_state.results)
    
    if st.button("Send to Google Sheets"):
        # Formatting results string
        res_str = ""
        for r in st.session_state.results:
            res_str += f"{r['Topic']}: {r['Status']}\n"
            
        payload = {
            "tutor": st.session_state.p_tutor,
            "student": st.session_state.p_student,
            "curriculum": st.session_state.p_curr,
            "grade": st.session_state.p_grade,
            "results": res_str
        }
        requests.post(WEBHOOK_URL, data=json.dumps(payload))
        st.success("Results Uploaded!")
