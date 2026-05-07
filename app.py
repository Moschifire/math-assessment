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

# --- UNIVERSAL IMAGE LOADER ---
def display_img(url, w=450, use_bytes=True):
    """Fetches image. If use_bytes is True, it returns the BytesIO object for custom layouts."""
    if not url or not isinstance(url, str) or len(url) < 10: return None
    try:
        f_url = url
        if 'drive.google.com' in url:
            f_id = url.split('/file/d/')[1].split('/')[0] if '/file/d/' in url else url.split('id=')[1].split('&')[0]
            f_url = f'https://drive.google.com/uc?export=download&id={f_id}'
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        res = requests.get(f_url, headers=headers, timeout=12)
        if res.status_code == 200:
            img_data = BytesIO(res.content)
            if use_bytes:
                return img_data
            else:
                st.image(img_data, width=w)
    except:
        return None

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
            if st.session_state.mastery_count >= len(curr_data) and g_idx < len(all_grades) - 1:
                st.session_state.p_grade = all_grades[g_idx + 1]
                st.session_state.set_idx = 0
                st.session_state.sub_idx = 0
                st.session_state.mastery_count = 0
                st.session_state.phase = "familiarity"
                st.session_state.bottleneck_active = True
                st.toast(f"Leveling up to {st.session_state.p_grade}!", icon="🚀")
            else: st.session_state.step = "summary"
    
    else: # ENGLISH LOGIC
        section = curr_data[st.session_state.set_idx]
        if st.session_state.sub_idx < len(section['questions']) - 1:
            st.session_state.sub_idx += 1
        elif st.session_state.set_idx < len(curr_data) - 1:
            st.session_state.set_idx += 1
            st.session_state.sub_idx = 0
            st.session_state.phase = "familiarity"
        else:
            if st.session_state.perfect_score and g_idx < len(all_grades) - 1:
                st.session_state.p_grade = all_grades[g_idx + 1]
                st.session_state.set_idx = 0
                st.session_state.sub_idx = 0
                st.session_state.phase = "familiarity"
                st.session_state.perfect_score = True
                st.session_state.bottleneck_active = True
                st.toast(f"Leveling up to {st.session_state.p_grade}!", icon="📚")
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

    elif st.session_state.phase in ["content", "mastery_retry", "subs"]:
        if subj == "Mathematics":
            if st.session_state.phase in ["content", "mastery_retry"]:
                lbl = "Mastery Question" if st.session_state.phase == "content" else "Mastery Question (Retry)"
                st.subheader(lbl)
                st.info(current_set['mastery_q'])
                display_img(current_set.get('image') or current_set.get('mastery_image'), w=500, use_bytes=False)
                if st.checkbox("Show Hint"): st.warning(current_set['mastery_hint'])
                c1, c2 = st.columns(2)
                if c1.button("✅ Correct"):
                    record(subj, grade, current_set['topic'], lbl, "Correct")
                    st.session_state.mastery_count += 1
                    advance_logic()
                if c2.button("❌ Incorrect"):
                    record(subj, grade, current_set['topic'], lbl, "Incorrect")
                    st.session_state.perfect_score = False
                    if st.session_state.bottleneck_active or st.session_state.phase == "mastery_retry": st.session_state.step = "summary"
                    else: st.session_state.phase = "subs"; st.session_state.sub_idx = 0
                    st.rerun()
            elif st.session_state.phase == "subs":
                sub = current_set['subs'][st.session_state.sub_idx]
                st.subheader(f"Sub-Question {st.session_state.sub_idx+1}")
                st.write(sub['q'])
                display_img(sub.get('image'), w=400, use_bytes=False)
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

        else: # ENGINE: ENGLISH
            st.header(current_set['section_title'])
            st.info(f"**Instruction:** {current_set['instruction']}")
            if current_set.get('content_text'): st.code(current_set['content_text'], language=None)
            display_img(current_set.get('image') or current_set.get('mastery_image'), w=500, use_bytes=False)
            
            q_list = current_set['questions']
            q = q_list[st.session_state.sub_idx]
            st.divider()
            st.subheader(f"Question {st.session_state.sub_idx + 1}")
            st.write(q['q'])
            
            # --- LOGIC FOR MULTIPLE IMAGES ---
            img_list = q.get('images') or []
            if isinstance(img_list, list) and len(img_list) > 0:
                cols = st.columns(len(img_list))
                for i, img_url in enumerate(img_list):
                    img_data = display_img(img_url, use_bytes=True)
                    if img_data: cols[i].image(img_data, use_container_width=True)
            elif q.get('image'):
                display_img(q.get('image'), w=400, use_bytes=False)
            
            if st.checkbox("Show Hint"): st.warning(q['h'])
            c1, c2 = st.columns(2)
            if c1.button("✅ Correct"):
                record(subj, grade, current_set['section_title'], f"Q{st.session_state.sub_idx+1}", "Correct")
                advance_logic()
            if c2.button("❌ Incorrect"):
                record(subj, grade, current_set['section_title'], f"Q{st.session_state.sub_idx+1}", "Incorrect")
                st.session_state.perfect_score = False
                if st.session_state.bottleneck_active: st.session_state.step = "summary"
                else: advance_logic()
                st.rerun()

elif st.session_state.step == "summary":
    st.header("Assessment Summary")
    df = pd.DataFrame(st.session_state.results)
    st.table(df)
    obs = st.text_area("Tutor Observations")
    if st.button("Final Submit"):
        payload = {"tutor": st.session_state.p_tutor, "student": st.session_state.p_student, "subject": st.session_state.p_subject, "curriculum": st.session_state.p_curr, "grade": st.session_state.p_grade, "results": df.to_string(), "feedback": obs}
        try:
            requests.post(WEBHOOK_URL, data=json.dumps(payload))
            st.success("Submitted!")
        except: st.error("Failed.")
    if st.button("New Assessment"):
        st.session_state.clear(); st.rerun()
