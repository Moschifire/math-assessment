import streamlit as st
import pandas as pd
import requests
import json
import os
import re
from io import BytesIO
from supabase import create_client, Client
from fpdf import FPDF

# --- CONFIG FROM SECRETS ---
def get_secret(key):
    return st.secrets.get(key.upper()) or st.secrets.get(key.lower())

SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD")

st.set_page_config(page_title="Multi-Subject Diagnostic Pro", layout="wide")

# --- INITIALIZE SUPABASE ---
@st.cache_resource
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY: return None
    try:
        return create_client(SUPABASE_URL.strip().rstrip("/"), SUPABASE_KEY.strip())
    except:
        return None

supabase = init_supabase()

# --- PDF GENERATOR FUNCTION (FIXED FOR FPDF2) ---
def create_pdf(data):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Title
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "Diagnostic Assessment & Learning Plan", ln=True, align="C")
        pdf.ln(5)
        
        # Student Info Header
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        student_name = str(data.get('student', 'N/A'))
        pdf.cell(0, 10, f" Student: {student_name} ", ln=True, fill=True)
        
        pdf.set_font("helvetica", "", 10)
        date_str = str(data.get('created_at', ''))[:10]
        pdf.cell(0, 8, f"Date: {date_str} | Subject: {data.get('subject', 'N/A')} | Grade: {data.get('grade', 'N/A')}", ln=True)
        pdf.cell(0, 8, f"Tutor: {data.get('tutor', 'N/A')} | Curriculum: {data.get('curriculum', 'N/A')}", ln=True)
        pdf.ln(5)
        
        # Diagnostic Results
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "Diagnostic Results Overview", ln=True)
        pdf.set_font("courier", "", 9)
        # Clean text for Latin-1 PDF encoding
        results_text = str(data.get('results', '')).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, results_text)
        pdf.ln(5)
        
        # AI Plan
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "Personalized 12-Week Learning Plan", ln=True)
        pdf.set_font("helvetica", "", 10)
        plan_text = str(data.get('ai_plan', 'No plan generated.')).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, plan_text)
        
        # output() in fpdf2 returns bytes directly
        return pdf.output()
    except Exception as e:
        st.error(f"PDF Generation Error: {e}")
        return None

# --- AI AGENT FUNCTION ---
def generate_ai_report(t_name, s_name, subj, grade, curr, res_text, tutor_fb):
    if not GEMINI_API_KEY: return "AI Error: Gemini Key missing."
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"Expert Diagnostician: Analyze {s_name} results for {subj} ({grade} - {curr}). Results: {res_text}. Tutor Notes: {tutor_fb}. Task: 1. Diagnostic Overview. 2. 12-Week Personal Plan Table."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(url, json=payload, timeout=30)
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: return "AI Plan generation failed."

# --- UNIVERSAL IMAGE LOADER ---
def display_img(url, w=450, return_bytes=False):
    if not url or not isinstance(url, str) or len(url) < 10: return None
    try:
        f_url = url
        if 'drive.google.com' in url:
            f_id = url.split('/file/d/')[1].split('/')[0] if '/file/d/' in url else url.split('id=')[1].split('&')[0]
            f_url = f'https://drive.google.com/uc?export=download&id={f_id}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(f_url, headers=headers, timeout=12)
        if res.status_code == 200:
            img_data = BytesIO(res.content)
            if return_bytes: return img_data
            else: st.image(img_data, width=w); return True
    except: return None

# --- DATA LOADER ---
def load_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f: return json.load(f)
    return {}
ALL_DATA = load_data()

# --- STATE MGMT ---
if 'step' not in st.session_state:
    st.session_state.update({
        "step": "setup", "results": [], "set_idx": 0, "sub_idx": 0, 
        "phase": "familiarity", "mastery_count": 0, "perfect_score": True, 
        "bottleneck_active": False, "ai_report": "", "admin_authenticated": False
    })

def record(subj, grade, topic, level, status):
    st.session_state.results.append({"Subject": subj, "Grade": grade, "Topic": topic, "Level": level, "Status": status})

def advance_logic():
    subj, grade_key = st.session_state.p_subject, st.session_state.p_grade
    curr_data = ALL_DATA[subj][st.session_state.p_curr][grade_key]
    all_grades = list(ALL_DATA[subj][st.session_state.p_curr].keys())
    g_idx = all_grades.index(grade_key)
    if subj == "Mathematics":
        if st.session_state.set_idx < len(curr_data) - 1:
            st.session_state.set_idx += 1; st.session_state.sub_idx = 0; st.session_state.phase = "familiarity"
        else:
            if st.session_state.mastery_count >= len(curr_data) and g_idx < len(all_grades)-1:
                st.session_state.update({"p_grade": all_grades[g_idx+1], "set_idx": 0, "sub_idx": 0, "mastery_count": 0, "phase": "familiarity", "bottleneck_active": True})
                st.toast("Leveling up!", icon="🚀")
            else: st.session_state.step = "summary"
    else:
        if st.session_state.sub_idx < len(curr_data[st.session_state.set_idx]['questions']) - 1:
            st.session_state.sub_idx += 1
        elif st.session_state.set_idx < len(curr_data) - 1:
            st.session_state.set_idx += 1; st.session_state.sub_idx = 0; st.session_state.phase = "familiarity"
        else:
            if st.session_state.perfect_score and g_idx < len(all_grades)-1:
                st.session_state.update({"p_grade": all_grades[g_idx+1], "set_idx": 0, "sub_idx": 0, "phase": "familiarity", "perfect_score": True, "bottleneck_active": True})
                st.toast("Leveling up!", icon="📚")
            else: st.session_state.step = "summary"
    st.rerun()

# --- NAVIGATION ---
page = st.sidebar.radio("Navigation", ["Take Assessment", "Admin Dashboard"])

# --- ADMIN DASHBOARD ---
if page == "Admin Dashboard":
    st.title("📊 Admin Dashboard")
    if not st.session_state.admin_authenticated:
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock Dashboard"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else: st.error("Wrong Password")
    else:
        if st.sidebar.button("Logout Admin"):
            st.session_state.admin_authenticated = False
            st.rerun()
            
        if not supabase: st.error("Supabase not connected.")
        else:
            try:
                res = supabase.table("assessment_results").select("*").order("created_at", desc=True).execute()
                if res.data:
                    df = pd.DataFrame(res.data)
                    st.dataframe(df[['created_at', 'student', 'subject', 'grade']], use_container_width=True)
                    st.divider()
                    sel = st.selectbox("Select Student Report:", df['student'].unique())
                    row = df[df['student'] == sel].iloc[0].to_dict() # Convert Series to Dict for create_pdf
                    
                    pdf_data = create_pdf(row)
                    if pdf_data:
                        st.download_button(label="📥 Download Report as PDF", data=pdf_data, file_name=f"Report_{sel}.pdf", mime="application/pdf")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("Diagnostic Results")
                        st.text(row.get('results', ''))
                        st.subheader("Tutor Feedback")
                        st.write(row.get('feedback', ''))
                    with c2:
                        st.subheader("AI 12-Week Plan")
                        st.markdown(row.get('ai_plan', ''))
                else: st.info("No records found.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- ASSESSMENT FLOW ---
elif page == "Take Assessment":
    if st.session_state.step == "setup":
        st.title("Diagnostic Setup")
        subjs = list(ALL_DATA.keys())
        s_subj = st.selectbox("Subject", subjs) if subjs else None
        if s_subj:
            currs = list(ALL_DATA[s_subj].keys())
            s_curr = st.selectbox("Curriculum", currs)
            if s_curr:
                grades = list(ALL_DATA[s_subj][s_curr].keys())
                s_grade = st.selectbox("Starting Grade", grades)
        t_tutor, t_student = st.text_input("Tutor Name"), st.text_input("Student Name")
        if st.button("Begin"):
            if t_tutor and t_student and s_grade:
                st.session_state.update({"p_tutor": t_tutor, "p_student": t_student, "p_subject": s_subj, "p_curr": s_curr, "p_grade": s_grade, "p_start_grade": s_grade, "step": "testing"})
                st.rerun()

    elif st.session_state.step == "testing":
        subj, grade = st.session_state.p_subject, st.session_state.p_grade
        content = ALL_DATA[subj][st.session_state.p_curr][grade]
        curr_set = content[st.session_state.set_idx]
        st.title(f"{subj}: {grade}"); st.divider()
        if st.session_state.phase == "familiarity":
            topic_lbl = curr_set.get('topic') or curr_set.get('section_title')
            st.header(topic_lbl)
            if st.button("Yes, proceed"): st.session_state.phase = "content"; st.rerun()
            if st.button("No, skip"):
                record(subj, grade, topic_lbl, "Familiarity", "No"); st.session_state.perfect_score = False
                if st.session_state.bottleneck_active: st.session_state.step = "summary"
                else: advance_logic()
                st.rerun()
        elif st.session_state.phase in ["content", "mastery_retry", "subs"]:
            if subj == "Mathematics":
                if st.session_state.phase in ["content", "mastery_retry"]:
                    lbl = "Mastery Q" if st.session_state.phase == "content" else "Mastery Q (Retry)"
                    st.info(curr_set['mastery_q']); display_img(curr_set.get('image') or curr_set.get('mastery_image'))
                    if st.button("✅ Correct"): record(subj, grade, curr_set['topic'], lbl, "Correct"); st.session_state.mastery_count += 1; advance_logic()
                    if st.button("❌ Incorrect"):
                        record(subj, grade, curr_set['topic'], lbl, "Incorrect"); st.session_state.perfect_score = False
                        if st.session_state.bottleneck_active or st.session_state.phase == "mastery_retry": st.session_state.step = "summary"
                        else: st.session_state.phase = "subs"; st.session_state.sub_idx = 0
                        st.rerun()
                elif st.session_state.phase == "subs":
                    sub = curr_set['subs'][st.session_state.sub_idx]
                    st.subheader(f"Sub-Q {st.session_state.sub_idx+1}"); st.write(sub['q']); display_img(sub.get('image'))
                    if st.button("✅ Correct"):
                        record(subj, grade, current_set['topic'] if 'current_set' in locals() else curr_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Correct")
                        if st.session_state.sub_idx < len(curr_set['subs'])-1: st.session_state.sub_idx += 1
                        else: st.session_state.phase = "mastery_retry"
                        st.rerun()
                    if st.button("❌ Incorrect"):
                        record(subj, grade, curr_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Incorrect"); st.session_state.perfect_score = False
                        if st.session_state.bottleneck_active: st.session_state.step = "summary"
                        else: advance_logic()
                        st.rerun()
            else: # English
                st.info(curr_set['instruction'])
                if curr_set.get('content_text'): st.code(curr_set['content_text'], language=None)
                display_img(curr_set.get('image') or curr_set.get('mastery_image'))
                q = curr_set['questions'][st.session_state.sub_idx]
                st.subheader(q['q'])
                imgs = q.get('images') or []
                if isinstance(imgs, list) and imgs:
                    cols = st.columns(len(imgs))
                    for i, u in enumerate(imgs):
                        b = display_img(u, return_bytes=True)
                        if b: cols[i].image(b, use_container_width=True)
                elif q.get('image'): display_img(q.get('image'))
                if st.button("✅ Correct"): record(subj, grade, curr_set['section_title'], f"Q{st.session_state.sub_idx+1}", "Correct"); advance_logic()
                if st.button("❌ Incorrect"):
                    record(subj, grade, curr_set['section_title'], f"Q{st.session_state.sub_idx+1}", "Incorrect"); st.session_state.perfect_score = False
                    if st.session_state.bottleneck_active: st.session_state.step = "summary"
                    else: advance_logic()
                    st.rerun()
    elif st.session_state.step == "summary":
        st.title("Summary")
        df = pd.DataFrame(st.session_state.results); st.table(df)
        obs = st.text_area("Tutor Feedback")
        if st.button("✨ Generate AI Plan"):
            st.session_state.ai_report = generate_ai_report(st.session_state.p_tutor, st.session_state.p_student, st.session_state.p_subject, st.session_state.p_grade, st.session_state.p_curr, df.to_string(), obs)
            st.markdown(st.session_state.ai_report)
        if st.button("💾 Save to Supabase"):
            payload = {"tutor": st.session_state.p_tutor, "student": st.session_state.p_student, "subject": st.session_state.p_subject, "curriculum": st.session_state.p_curr, "grade": st.session_state.p_grade, "results": df.to_string(), "feedback": obs, "ai_plan": st.session_state.ai_report}
            try: supabase.table("assessment_results").insert(payload).execute(); st.success("Saved!")
            except Exception as e: st.error(f"Error: {e}")
