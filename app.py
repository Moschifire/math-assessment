import streamlit as st
import pandas as pd
import requests
import json
import os

# --- CONFIG ---
# PASTE YOUR GOOGLE APPS SCRIPT URL HERE
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxFm533cRPJWr3e-XBb0iHWoTJhKi0eERBGxXCJ_rkpMJP1fIyKPh4VmU2xE2F1aTr51g/exec" 

st.set_page_config(page_title="Math Diagnostic Assessment", layout="wide")

# --- HELPER: GOOGLE DRIVE IMAGE CONVERTER ---
def get_google_drive_direct_url(url):
    """Converts a standard Google Drive share link into a direct image link."""
    if not url or 'drive.google.com' not in url:
        return url
    try:
        # Handle links like /file/d/[ID]/view
        if '/file/d/' in url:
            file_id = url.split('/file/d/')[1].split('/')[0]
        # Handle links like ?id=[ID]
        elif 'id=' in url:
            file_id = url.split('id=')[1].split('&')[0]
        else:
            return url
        return f'https://drive.google.com/uc?export=view&id={file_id}'
    except Exception:
        return url

# --- DATA LOADER ---
def load_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f:
            return json.load(f)
    else:
        st.error("Missing 'content.json'. Please ensure it exists in your repository.")
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
    st.session_state.bottleneck_active = False # Becomes True if they advance to a higher grade

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
    st.title("Mathematics Diagnostic Assessment Setup")
    
    if not ALL_CONTENT:
        st.stop()

    t_tutor = st.text_input("Tutor Name")
    t_student = st.text_input("Student Name")
    
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
            st.session_state.step = "testing"
            st.rerun()
        else:
            st.error("Please enter both the Tutor and Student names.")

# --- UI: TESTING ---
elif st.session_state.step == "testing":
    grade_data = ALL_CONTENT[st.session_state.p_curr][st.session_state.p_grade]
    current_set = grade_data[st.session_state.set_idx]
    
    st.title(f"Diagnostic: {st.session_state.p_grade}")
    st.caption(f"Tutor: {st.session_state.p_tutor} | Student: {st.session_state.p_student}")
    st.divider()

    # PHASE 1: FAMILIARITY CHECK
    if st.session_state.phase == "familiarity":
        st.header(current_set['topic'])
        st.subheader("Is the student familiar with this topic?")
        c1, c2 = st.columns(2)
        if c1.button("Yes, proceed"):
            st.session_state.phase = "mastery"
            st.rerun()
        if c2.button("No, skip topic"):
            record_entry(current_set['topic'], "Familiarity Check", "Not Familiar", False)
            
            # BOTTLENECK: End assessment if this is an advanced grade
            if st.session_state.bottleneck_active:
                st.session_state.step = "summary"
            else:
                if st.session_state.set_idx < len(grade_data) - 1:
                    st.session_state.set_idx += 1
                else:
                    st.session_state.step = "summary"
            st.rerun()

    # PHASE 2: MASTERY QUESTION
    elif st.session_state.phase == "mastery":
        st.subheader("Mastery Level Question")
        st.info(current_set['mastery_q'])
        
        # Display converted image
        if current_set.get('image'):
            st.image(get_google_drive_direct_url(current_set['image']), use_container_width=True)
            
        h_used = st.checkbox("Student requested a hint?")
        if h_used:
            st.warning(current_set['mastery_hint'])
        
        st.divider()
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(current_set['topic'], "Mastery Q", "Correct", h_used)
            st.session_state.mastery_count += 1
            
            # Move to next set within current grade
            if st.session_state.set_idx < len(grade_data) - 1:
                st.session_state.set_idx += 1
                st.session_state.phase = "familiarity"
            else:
                # End of Grade: Check for Advance
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
            # BOTTLENECK: End assessment if they fail in an advanced grade
            if st.session_state.bottleneck_active:
                st.session_state.step = "summary"
            else:
                st.session_state.phase = "subs"
                st.session_state.sub_idx = 0
            st.rerun()

    # PHASE 3: SUB-QUESTIONS
    elif st.session_state.phase == "subs":
        sub_list = current_set['subs']
        sub = sub_list[st.session_state.sub_idx]
        st.subheader(f"Diving Deeper: Sub-Question {st.session_state.sub_idx + 1}")
        st.write(sub['q'])
        
        if sub.get('image'):
            st.image(get_google_drive_direct_url(sub['image']), use_container_width=True)
            
        h_used = st.checkbox(f"Show hint for sub-question?")
        if h_used:
            st.warning(sub['h'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Next/Correct"):
            record_entry(current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Correct", h_used)
            if st.session_state.sub_idx < len(sub_list) - 1:
                st.session_state.sub_idx += 1
            else:
                # Finished subs for this set
                if st.session_state.set_idx < len(grade_data) - 1:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()
            
        if c2.button("❌ Incorrect"):
            record_entry(current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Incorrect", h_used)
            if st.session_state.sub_idx < len(sub_list) - 1:
                st.session_state.sub_idx += 1
            else:
                if st.session_state.set_idx < len(grade_data) - 1:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()

# --- UI: SUMMARY & SUBMISSION ---
elif st.session_state.step == "summary":
    st.header("Diagnostic Assessment Results")
    final_df = pd.DataFrame(st.session_state.results)
    st.table(final_df)
    
    # Format detailed report for Google Sheet
    report_body = f"Math Assessment Summary for {st.session_state.p_student}\n"
    report_body += "-"*30 + "\n"
    for r in st.session_state.results:
        report_body += f"[{r['Grade']}] {r['Topic']} | {r['Level']}: {r['Status']} (Hint: {r['Hint']})\n"

    if st.button("Submit Report to Google Sheets"):
        payload = {
            "tutor": st.session_state.p_tutor,
            "student": st.session_state.p_student,
            "curriculum": st.session_state.p_curr,
            "grade": st.session_state.p_grade,
            "results": report_body
        }
        try:
            r = requests.post(WEBHOOK_URL, data=json.dumps(payload))
            if r.status_code == 200:
                st.success("Successfully submitted to Google Sheets!")
            else:
                st.error(f"Error: Server responded with status {r.status_code}")
        except Exception as e:
            st.error(f"Submission failed: {str(e)}")
    
    if st.button("Start New Assessment"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
