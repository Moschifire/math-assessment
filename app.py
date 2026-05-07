import streamlit as st
import pandas as pd
import requests
import json
import os
from io import BytesIO

# --- CONFIG ---
# Replace with your actual URL
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyZU-Km741xhQuKc9W98-xFGsaEQ18P2LgRKlCSNEKZDzYoXrqgpEA04WMoFLeq_WRpFQ/exec" 

st.set_page_config(page_title="Math Diagnostic Assessment", layout="wide")

# --- DATA LOADER (Cached to prevent reload issues) ---
@st.cache_data
def load_assessment_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f:
            return json.load(f)
    return {}

ALL_CONTENT = load_assessment_data()

# --- HELPER: IMAGE LOADER ---
def display_assessment_image(url, img_width=400):
    if not url or not isinstance(url, str) or len(url) < 10:
        return
    try:
        final_url = url
        if 'drive.google.com' in url:
            file_id = None
            if '/file/d/' in url: file_id = url.split('/file/d/')[1].split('/')[0]
            elif 'id=' in url: file_id = url.split('id=')[1].split('&')[0]
            if file_id: final_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(final_url, headers=headers, timeout=10)
        if response.status_code == 200:
            st.image(BytesIO(response.content), width=img_width)
    except:
        pass

# --- INITIALIZE SESSION STATE ---
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

def advance_logic():
    """Handles the move to next question set or next grade."""
    curr_data = ALL_CONTENT.get(st.session_state.p_curr, {}).get(st.session_state.p_grade, [])
    
    # 1. Check if we have more questions in the current grade
    if st.session_state.set_idx < len(curr_data) - 1:
        st.session_state.set_idx += 1
        st.session_state.sub_idx = 0
        st.session_state.phase = "familiarity"
        st.rerun()
    
    # 2. End of the current grade questions reached
    else:
        # Mastery Check: Did they answer all Mastery Qs correctly in this grade?
        if st.session_state.mastery_count == len(curr_data):
            all_grades = list(ALL_CONTENT.get(st.session_state.p_curr, {}).keys())
            try:
                current_g_idx = all_grades.index(st.session_state.p_grade)
                if current_g_idx < len(all_grades) - 1:
                    # Transition to next grade
                    st.session_state.p_grade = all_grades[current_g_idx + 1]
                    st.session_state.set_idx = 0
                    st.session_state.sub_idx = 0
                    st.session_state.mastery_count = 0
                    st.session_state.phase = "familiarity"
                    st.session_state.bottleneck_active = True
                    st.toast(f"Transitioning to {st.session_state.p_grade}!", icon="🚀")
                    st.rerun()
                else:
                    st.session_state.step = "summary"
                    st.rerun()
            except ValueError:
                st.session_state.step = "summary"
                st.rerun()
        else:
            # Bottleneck: No perfect mastery, end assessment
            st.session_state.step = "summary"
            st.rerun()

# --- APP FLOW ---

# 1. SETUP
if st.session_state.step == "setup":
    st.title("Math Diagnostic: Setup")
    if not ALL_CONTENT:
        st.error("Data file 'content.json' not found or empty.")
        st.stop()
        
    t_tutor = st.text_input("Tutor Name")
    t_student = st.text_input("Student Name")
    t_curr = st.selectbox("Curriculum", list(ALL_CONTENT.keys()))
    if t_curr:
        t_grade = st.selectbox("Starting Grade", list(ALL_CONTENT[t_curr].keys()))
    
    if st.button("Start Assessment"):
        if t_tutor and t_student:
            st.session_state.p_tutor = t_tutor
            st.session_state.p_student = t_student
            st.session_state.p_curr = t_curr
            st.session_state.p_grade = t_grade
            st.session_state.step = "testing"
            st.rerun()
        else:
            st.error("Please fill in both names.")

# 2. TESTING
elif st.session_state.step == "testing":
    # Defensive lookup
    grade_data = ALL_CONTENT.get(st.session_state.p_curr, {}).get(st.session_state.p_grade, [])
    if not grade_data or st.session_state.set_idx >= len(grade_data):
        st.error("Grade data error. Ending assessment.")
        if st.button("View Results"): st.session_state.step = "summary"; st.rerun()
        st.stop()

    current_set = grade_data[st.session_state.set_idx]
    st.title(f"Class: {st.session_state.p_grade}")
    st.caption(f"Student: {st.session_state.p_student} | Tutor: {st.session_state.p_tutor}")
    st.divider()

    if st.session_state.phase == "familiarity":
        st.header(current_set.get('topic', 'Topic'))
        st.subheader("Is the student familiar with this topic?")
        c1, c2 = st.columns(2)
        if c1.button("Yes"):
            st.session_state.phase = "mastery"
            st.rerun()
        if c2.button("No"):
            record_entry(current_set['topic'], "Familiarity Check", "Not Familiar", False)
            if st.session_state.bottleneck_active:
                st.session_state.step = "summary"
                st.rerun()
            else:
                advance_logic()

    elif st.session_state.phase in ["mastery", "mastery_retry"]:
        label = "Mastery Question" if st.session_state.phase == "mastery" else "Mastery Question (Retry)"
        st.subheader(label)
        st.info(current_set.get('mastery_q', 'No Question Text'))
        m_img = current_set.get('image') or current_set.get('mastery_image')
        display_assessment_image(m_img, img_width=500)
        h_used = st.checkbox("Show Hint?")
        if h_used: st.warning(current_set.get('mastery_hint', 'No Hint available'))
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(current_set['topic'], label, "Correct", h_used)
            st.session_state.mastery_count += 1
            advance_logic()
        if c2.button("❌ Incorrect"):
            record_entry(current_set['topic'], label, "Incorrect", h_used)
            if st.session_state.bottleneck_active or st.session_state.phase == "mastery_retry":
                st.session_state.step = "summary"
                st.rerun()
            else:
                st.session_state.phase = "subs"
                st.session_state.sub_idx = 0
                st.rerun()

    elif st.session_state.phase == "subs":
        subs = current_set.get('subs', [])
        if not subs: 
            st.session_state.phase = "mastery_retry"; st.rerun()
        
        sub = subs[st.session_state.sub_idx]
        st.subheader(f"Sub-Question {st.session_state.sub_idx + 1}")
        st.write(sub.get('q', 'No Question Text'))
        display_assessment_image(sub.get('image'), img_width=400)
        h_used = st.checkbox(f"Show hint?")
        if h_used: st.warning(sub.get('h', 'No hint available'))
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Correct", h_used)
            if st.session_state.sub_idx < len(subs) - 1:
                st.session_state.sub_idx += 1
                st.rerun()
            else:
                st.session_state.phase = "mastery_retry"
                st.rerun()
        if c2.button("❌ Incorrect"):
            record_entry(current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Incorrect", h_used)
            if st.session_state.bottleneck_active:
                st.session_state.step = "summary"
            else:
                advance_logic()
            st.rerun()

# 3. SUMMARY
elif st.session_state.step == "summary":
    st.header("Assessment Summary")
    if not st.session_state.results:
        st.write("No questions were attempted.")
    else:
        st.table(pd.DataFrame(st.session_state.results))
    
    st.divider()
    tutor_obs = st.text_area("Tutor Observations & Feedback")
    
    if st.button("Final Submit to Google Sheets"):
        report_body = "\n".join([f"[{r['Grade']}] {r['Topic']} | {r['Level']}: {r['Status']}" for r in st.session_state.results])
        payload = {
            "tutor": st.session_state.p_tutor, 
            "student": st.session_state.p_student, 
            "results": report_body,
            "curriculum": st.session_state.p_curr,
            "grade": st.session_state.p_grade,
            "feedback": tutor_obs
        }
        try:
            requests.post(WEBHOOK_URL, data=json.dumps(payload))
            st.success("Successfully Submitted!")
        except: st.error("Submission failed.")
    
    if st.button("Start New Assessment"):
        st.session_state.clear()
        st.rerun()
