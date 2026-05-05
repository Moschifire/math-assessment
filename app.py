import streamlit as st
import pandas as pd
import requests
import json
import os

# --- CONFIG ---
# PASTE YOUR GOOGLE APPS SCRIPT URL HERE
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxFm533cRPJWr3e-XBb0iHWoTJhKi0eERBGxXCJ_rkpMJP1fIyKPh4VmU2xE2F1aTr51g/exec" 

st.set_page_config(page_title="Math Diagnostic Pro", layout="wide")

# --- DATA LOADER ---
def load_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f:
            return json.load(f)
    else:
        st.error("Missing 'content.json'. Please create it in your repository.")
        return {}

ALL_CONTENT = load_data()

# --- INITIALIZE STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.p_tutor = ""
    st.session_state.p_student = ""
    st.session_state.p_curr = "US Common Core"
    st.session_state.p_grade = "Kindergarten"
    st.session_state.start_grade = ""
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    st.session_state.phase = "familiarity"
    st.session_state.results = []
    st.session_state.mastery_count = 0
    st.session_state.bottleneck_active = False # Activated if they advanced a grade

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
    
    # Selection from JSON keys
    curriculums = list(ALL_CONTENT.keys())
    t_curr = st.selectbox("Select Curriculum", curriculums)
    
    if t_curr:
        grades = list(ALL_CONTENT[t_curr].keys())
        t_grade = st.selectbox("Select Starting Class", grades)
    
    if st.button("Begin Assessment"):
        if t_tutor and t_student:
            st.session_state.p_tutor = t_tutor
            st.session_state.p_student = t_student
            st.session_state.p_curr = t_curr
            st.session_state.p_grade = t_grade
            st.session_state.start_grade = t_grade
            st.session_state.step = "testing"
            st.rerun()
        else:
            st.error("Please enter names.")

# --- UI: TESTING ---
elif st.session_state.step == "testing":
    grade_data = ALL_CONTENT[st.session_state.p_curr][st.session_state.p_grade]
    current_set = grade_data[st.session_state.set_idx]
    
    st.title(f"Diagnostic: {st.session_state.p_grade}")
    st.caption(f"Tutor: {st.session_state.p_tutor} | Student: {st.session_state.p_student}")

    if st.session_state.phase == "familiarity":
        st.subheader(current_set['topic'])
        st.write("Is the student familiar with this topic?")
        c1, c2 = st.columns(2)
        if c1.button("Yes"):
            st.session_state.phase = "mastery"
            st.rerun()
        if c2.button("No"):
            record_entry(current_set['topic'], "Familiarity", "Not Familiar", False)
            # BOTTLENECK RULE: End if this is a "next class"
            if st.session_state.bottleneck_active:
                st.session_state.step = "summary"
            else:
                if st.session_state.set_idx < len(grade_data) - 1:
                    st.session_state.set_idx += 1
                else:
                    st.session_state.step = "summary"
            st.rerun()

    elif st.session_state.phase == "mastery":
        st.subheader("Mastery Question")
        st.info(current_set['mastery_q'])
        
        if current_set.get('image'):
            st.image(current_set['image'], use_container_width=True)
            
        h_used = st.checkbox("Show Hint?")
        if h_used: st.warning(current_set['mastery_hint'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(current_set['topic'], "Mastery Q", "Correct", h_used)
            st.session_state.mastery_count += 1
            
            # ADVANCE LOGIC
            if st.session_state.set_idx < len(grade_data) - 1:
                st.session_state.set_idx += 1
                st.session_state.phase = "familiarity"
            else:
                # End of 5 questions: Check for Grade Advance
                if st.session_state.mastery_count == 5:
                    all_grades = list(ALL_CONTENT[st.session_state.p_curr].keys())
                    current_g_idx = all_grades.index(st.session_state.p_grade)
                    
                    if current_g_idx < len(all_grades) - 1:
                        st.session_state.p_grade = all_grades[current_g_idx + 1]
                        st.session_state.set_idx = 0
                        st.session_state.mastery_count = 0
                        st.session_state.bottleneck_active = True
                        st.session_state.phase = "familiarity"
                        st.success(f"Advancing to {st.session_state.p_grade}...")
                    else: st.session_state.step = "summary"
                else: st.session_state.step = "summary"
            st.rerun()
            
        if c2.button("❌ Incorrect"):
            record_entry(current_set['topic'], "Mastery Q", "Incorrect", h_used)
            # BOTTLENECK RULE: End assessment if in "next class"
            if st.session_state.bottleneck_active:
                st.session_state.step = "summary"
            else:
                st.session_state.phase = "subs"
                st.session_state.sub_idx = 0
            st.rerun()

    elif st.session_state.phase == "subs":
        sub = current_set['subs'][st.session_state.sub_idx]
        st.subheader(f"Sub-Question {st.session_state.sub_idx + 1}")
        st.write(sub['q'])
        
        if sub.get('image'): st.image(sub['image'], use_container_width=True)
        h_used = st.checkbox(f"Hint for Sub {st.session_state.sub_idx + 1}?")
        if h_used: st.warning(sub['h'])
        
        c1, c2 = st.columns(2)
        if c1.button("Next Correct"):
            record_entry(current_set['topic'], f"Sub-{st.session_state.sub_idx + 1}", "Correct", h_used)
            if st.session_state.sub_idx < len(current_set['subs']) - 1:
                st.session_state.sub_idx += 1
            else:
                if st.session_state.set_idx < len(grade_data) - 1:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()
        if c2.button("Next Incorrect"):
            record_entry(current_set['topic'], f"Sub-{st.session_state.sub_idx + 1}", "Incorrect", h_used)
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
    final_df = pd.DataFrame(st.session_state.results)
    st.table(final_df)
    
    report_text = ""
    for r in st.session_state.results:
        report_text += f"[{r['Grade']}] {r['Topic']} | {r['Level']}: {r['Status']} (Hint: {r['Hint']})\n"

    if st.button("Final Submit"):
        payload = {
            "tutor": st.session_state.p_tutor,
            "student": st.session_state.p_student,
            "curriculum": st.session_state.p_curr,
            "grade": st.session_state.p_grade,
            "results": report_text
        }
        try:
            requests.post(WEBHOOK_URL, data=json.dumps(payload))
            st.success("Results synced to Google Sheets!")
        except:
            st.error("Submission failed.")
