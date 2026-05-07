import streamlit as st
import pandas as pd
import requests
import json
import os
from io import BytesIO

# --- CONFIG ---
WEBHOOK_URL = "https://script.google.com/macros/s/XXXX/exec" 

st.set_page_config(page_title="Multi-Subject Diagnostic", layout="wide")

# --- DATA LOADER ---
@st.cache_data
def load_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f:
            return json.load(f)
    return {}

ALL_DATA = load_data()

# --- HELPER: UNIVERSAL IMAGE LOADER ---
def display_img(url, img_width=400):
    if not url or not isinstance(url, str) or len(url) < 10:
        return
    try:
        f_url = url
        if 'drive.google.com' in url:
            f_id = url.split('/file/d/')[1].split('/')[0] if '/file/d/' in url else url.split('id=')[1].split('&')[0]
            f_url = f'https://drive.google.com/uc?export=download&id={f_id}'
        res = requests.get(f_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if res.status_code == 200:
            st.image(BytesIO(res.content), width=img_width)
    except:
        pass

# --- INITIALIZE STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.results = []
    # Logic States
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    st.session_state.phase = "familiarity" 
    st.session_state.mastery_count = 0
    st.session_state.bottleneck_active = False

def record_entry(subj, grade, topic, detail, status):
    st.session_state.results.append({
        "Subject": subj,
        "Grade": grade,
        "Topic": topic,
        "Level": detail,
        "Status": status
    })

# --- UI: SETUP ---
if st.session_state.step == "setup":
    st.title("Diagnostic Assessment Setup")
    
    # 1. Subject
    subjects = list(ALL_DATA.keys())
    selected_subject = st.selectbox("Select Subject", subjects, key="subj_select")
    
    # 2. Curriculum (defensive)
    if selected_subject:
        curriculums = list(ALL_DATA[selected_subject].keys())
        selected_curr = st.selectbox("Select Curriculum", curriculums, key="curr_select")
        
        # 3. Grade (defensive)
        if selected_curr:
            grades = list(ALL_DATA[selected_subject][selected_curr].keys())
            selected_grade = st.selectbox("Select Grade/Class", grades, key="grade_select")

    t_tutor = st.text_input("Tutor Name")
    t_student = st.text_input("Student Name")

    if st.button("Begin Assessment"):
        if t_tutor and t_student:
            st.session_state.p_tutor = t_tutor
            st.session_state.p_student = t_student
            st.session_state.p_subj = selected_subject
            st.session_state.p_curr = selected_curr
            st.session_state.p_grade = selected_grade
            st.session_state.step = "testing"
            st.rerun()
        else:
            st.error("Please enter names.")

# --- UI: TESTING ---
elif st.session_state.step == "testing":
    subj = st.session_state.p_subj
    grade = st.session_state.p_grade
    content = ALL_DATA[subj][st.session_state.p_curr][grade]
    
    st.title(f"{subj}: {grade}")
    st.caption(f"Tutor: {st.session_state.p_tutor} | Student: {st.session_state.p_student}")
    st.divider()

    # --- ENGINE 1: MATHEMATICS (Mastery-Scaffold Logic) ---
    if subj == "Mathematics":
        current_set = content[st.session_state.set_idx]
        
        if st.session_state.phase == "familiarity":
            st.header(current_set['topic'])
            st.subheader("Is the student familiar with this topic?")
            c1, c2 = st.columns(2)
            if c1.button("Yes"):
                st.session_state.phase = "mastery"
                st.rerun()
            if c2.button("No"):
                record_entry(subj, grade, current_set['topic'], "Familiarity", "Not Familiar")
                if st.session_state.bottleneck_active: st.session_state.step = "summary"
                else: 
                    if st.session_state.set_idx < len(content)-1: st.session_state.set_idx += 1
                    else: st.session_state.step = "summary"
                st.rerun()

        elif st.session_state.phase in ["mastery", "mastery_retry"]:
            label = "Mastery Question" if st.session_state.phase == "mastery" else "Mastery Question (Retry)"
            st.subheader(label)
            st.info(current_set['mastery_q'])
            display_img(current_set.get('image'), 500)
            if st.checkbox("Show Hint"): st.warning(current_set['mastery_hint'])
            
            c1, c2 = st.columns(2)
            if c1.button("✅ Correct"):
                record_entry(subj, grade, current_set['topic'], label, "Correct")
                st.session_state.mastery_count += 1
                # Advance Grade Logic
                if st.session_state.set_idx < len(content)-1:
                    st.session_state.set_idx += 1; st.session_state.phase = "familiarity"
                elif st.session_state.mastery_count == len(content):
                    all_grades = list(ALL_DATA[subj][st.session_state.p_curr].keys())
                    g_idx = all_grades.index(grade)
                    if g_idx < len(all_grades)-1:
                        st.session_state.p_grade = all_grades[g_idx+1]; st.session_state.set_idx = 0
                        st.session_state.mastery_count = 0; st.session_state.bottleneck_active = True
                        st.session_state.phase = "familiarity"; st.success("Advancing!")
                    else: st.session_state.step = "summary"
                else: st.session_state.step = "summary"
                st.rerun()
            if c2.button("❌ Incorrect"):
                record_entry(subj, grade, current_set['topic'], label, "Incorrect")
                if st.session_state.bottleneck_active or st.session_state.phase == "mastery_retry":
                    st.session_state.step = "summary"
                else:
                    st.session_state.phase = "subs"; st.session_state.sub_idx = 0
                st.rerun()

        elif st.session_state.phase == "subs":
            sub = current_set['subs'][st.session_state.sub_idx]
            st.subheader(f"Sub-Question {st.session_state.sub_idx+1}")
            st.write(sub['q'])
            display_img(sub.get('image'), 400)
            c1, c2 = st.columns(2)
            if c1.button("✅ Correct"):
                record_entry(subj, grade, current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Correct")
                if st.session_state.sub_idx < len(current_set['subs'])-1: st.session_state.sub_idx += 1
                else: st.session_state.phase = "mastery_retry"
                st.rerun()
            if c2.button("❌ Incorrect"):
                record_entry(subj, grade, current_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Incorrect")
                if st.session_state.set_idx < len(content)-1: 
                    st.session_state.set_idx += 1; st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
                st.rerun()

    # --- ENGINE 2: ENGLISH LANGUAGE (Sequential Section Logic) ---
    elif subj == "English Language":
        section = content[st.session_state.set_idx] # In English, set_idx is Section Index
        st.header(section['section_title'])
        st.info(section['instruction'])
        if section.get('content_text'):
            st.markdown(f"**Material:**\n\n {section['content_text']}")
        display_img(section.get('image'), 500)
        st.divider()
        
        q_list = section['questions']
        q = q_list[st.session_state.sub_idx] # In English, sub_idx is Question Index
        st.subheader(f"Question {st.session_state.sub_idx + 1}")
        st.write(q['q'])
        if st.checkbox("Show Hint"): st.warning(q['h'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(subj, grade, section['section_title'], f"Q{st.session_state.sub_idx+1}", "Correct")
            if st.session_state.sub_idx < len(q_list) - 1:
                st.session_state.sub_idx += 1
            elif st.session_state.set_idx < len(content) - 1:
                st.session_state.set_idx += 1; st.session_state.sub_idx = 0
            else: st.session_state.step = "summary"
            st.rerun()
        if c2.button("❌ Incorrect"):
            record_entry(subj, grade, section['section_title'], f"Q{st.session_state.sub_idx+1}", "Incorrect")
            # In English, if they fail, we typically bottleneck immediately
            st.session_state.step = "summary"
            st.rerun()

# --- UI: SUMMARY ---
elif st.session_state.step == "summary":
    st.header("Assessment Results")
    res_df = pd.DataFrame(st.session_state.results)
    st.table(res_df)
    obs = st.text_area("Tutor Observations")
    if st.button("Final Submit"):
        report = res_df.to_string()
        payload = {
            "tutor": st.session_state.p_tutor,
            "student": st.session_state.p_student,
            "subject": st.session_state.p_subj,
            "results": report,
            "feedback": obs
        }
        try:
            requests.post(WEBHOOK_URL, data=json.dumps(payload))
            st.success("Submitted!")
        except: st.error("Failed.")
