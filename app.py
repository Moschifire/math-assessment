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
    if not SUPABASE_URL or not SUPABASE_KEY: 
        return None
    try:
        return create_client(SUPABASE_URL.strip().rstrip("/"), SUPABASE_KEY.strip())
    except:
        return None

supabase = init_supabase()

# --- PDF HELPERS ---
def clean_txt(text):
    """Deep clean text for FPDF Latin-1 encoding."""
    if not text: 
        return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1').replace('?', '-')

def split_ai_content(text):
    """Separates the text overview from the markdown table."""
    lines = text.strip().split('\n')
    report_text, table_rows, in_table = [], [], False
    for line in lines:
        if line.strip().startswith('|'):
            in_table = True
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if not all(re.match(r'^-+$', p) for p in parts): 
                table_rows.append(parts)
        else:
            if not in_table: 
                report_text.append(line.replace('**', '').replace('###', '').strip())
    return "\n".join(report_text), table_rows

# --- PDF GENERATOR 1: ORIGINAL DETAILED TUTOR REPORT ---
def create_detailed_pdf(data):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Internal Diagnostic Assessment Log", ln=True, align="C")
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, f"Student: {data['student']} | Subject: {data['subject']} | Date: {str(data['created_at'])[:10]}", ln=True)
    pdf.ln(5)
    
    l_col, r_col = 85, 180
    curr_y = pdf.get_y()
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(l_col, 8, "Assessment Log", ln=True)
    pdf.set_font("courier", "", 8)
    pdf.multi_cell(l_col, 4, clean_txt(data.get('results', '')))
    
    pdf.set_y(curr_y)
    pdf.set_x(l_col + 15)
    overview, table = split_ai_content(data.get('ai_plan', ''))
    pdf.set_font("helvetica", "B", 12)
    pdf.set_x(l_col + 15)
    pdf.cell(r_col, 8, "AI Plan Overview", ln=True)
    pdf.set_font("helvetica", "", 9)
    pdf.set_x(l_col + 15)
    pdf.multi_cell(r_col, 5, clean_txt(overview))
    return bytes(pdf.output())

# --- PDF GENERATOR 2: STYLED PARENT DIAGNOSTIC REPORT ---
def create_parent_report_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # Branding
    pdf.set_fill_color(77, 208, 225) 
    pdf.rect(160, 10, 40, 10, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.text(168, 17, "GRADELY")
    
    # Header
    pdf.set_text_color(0, 151, 167)
    pdf.set_font("helvetica", "B", 24)
    pdf.text(20, 25, data['subject'])
    pdf.set_font("helvetica", "", 12)
    pdf.text(20, 32, "DIAGNOSTIC TEST")
    
    # Summary Box
    pdf.set_fill_color(26, 82, 118) 
    pdf.rect(15, 45, 180, 40, 'F')
    pdf.set_fill_color(255, 255, 255)
    pdf.circle(35, 65, 12, 'F') 
    
    pdf.set_xy(55, 50)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(255, 255, 255)
    overview, _ = split_ai_content(data.get('ai_plan', ''))
    summary = ". ".join(overview.split('.')[:3]) + "."
    pdf.multi_cell(135, 5, clean_txt(summary))
    
    # Skills Section
    pdf.set_xy(15, 95)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "SKILLS TESTED", ln=True)
    
    # Skill Cards
    results_list = data['results'].split('\n')
    pdf.set_font("helvetica", "", 10)
    for line in results_list:
        if '|' in line and ("Correct" in line or "Incorrect" in line):
            pdf.set_fill_color(245, 245, 245)
            pdf.rect(15, pdf.get_y(), 180, 15, 'F')
            pdf.set_x(20)
            skill = line.split('|')[1].split(':')[0].strip()
            status = "Mastered" if "Correct" in line else "Developing"
            pdf.set_text_color(0,0,0)
            pdf.cell(100, 15, clean_txt(skill))
            pdf.set_text_color(255, 193, 7)
            stars = "★ ★ ★" if status == "Mastered" else "★ ☆ ☆"
            pdf.cell(0, 15, stars, align="R", ln=True)
            pdf.ln(2)
            if pdf.get_y() > 260: 
                pdf.add_page()
            
    return bytes(pdf.output())

# --- PDF GENERATOR 3: STYLED LEARNING PATH ---
def create_learning_path_pdf(data):
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_fill_color(224, 247, 250)
    pdf.rect(0,0,297,210,'F')
    
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(15, 15, 70, 25, 'F')
    pdf.set_text_color(0,0,0)
    pdf.set_font("helvetica", "B", 8)
    pdf.text(20, 22, f"Name: {data['student']}")
    pdf.text(20, 27, f"Class: {data['grade']}")
    pdf.text(20, 32, f"Subject: {data['subject']}")
    
    pdf.set_font("helvetica", "B", 22)
    pdf.set_text_color(26, 82, 118)
    pdf.text(110, 25, "Your Learning Path")
    pdf.set_font("helvetica", "I", 12)
    pdf.text(115, 32, "[for the next 12 weeks]")
    
    _, table = split_ai_content(data.get('ai_plan', ''))
    pdf.set_xy(15, 50)
    if table:
        with pdf.table(width=270, line_height=7) as t:
            for row in table[:13]:
                r = t.row()
                for cell in row: 
                    r.cell(clean_txt(cell))
    
    return bytes(pdf.output())

# --- AI AGENT ---
def generate_ai_report(t_name, s_name, subj, grade, curr, res_text, tutor_fb):
    if not GEMINI_API_KEY: 
        return "Gemini Key missing."
    models = ["gemini-2.5-flash", "gemini-2.0-flash-exp"]
    prompt = f"Expert Diagnostician: Analyze {s_name} results for {subj} ({grade} - {curr}). Results: {res_text}. Tutor Notes: {tutor_fb}. Task: 1. DIAGNOSTIC OVERVIEW (encouraging parent-facing tone). 2. 12-WEEK PLAN Table."
    payload = {"contents": [{"parts": [{"text": prompt}]}], "safetySettings": [{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]}
    for m in models:
        url = f"https://generativelanguage.googleapis.com/v1/models/{m}:generateContent?key={GEMINI_API_KEY}"
        try:
            r = requests.post(url, json=payload, timeout=30)
            if r.status_code == 200: 
                return r.json()['candidates'][0]['content']['parts'][0]['text']
        except: 
            continue
    return "AI Busy."

# --- UNIVERSAL IMAGE LOADER ---
def display_img(url, w=450, return_bytes=False):
    if not url or not isinstance(url, str) or len(url) < 10: 
        return None
    try:
        f_url = url
        if 'drive.google.com' in url:
            f_id = url.split('/file/d/')[1].split('/')[0] if '/file/d/' in url else url.split('id=')[1].split('&')[0]
            f_url = f'https://drive.google.com/uc?export=download&id={f_id}'
        res = requests.get(f_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}, timeout=12)
        if res.status_code == 200:
            img_data = BytesIO(res.content)
            if return_bytes: 
                return img_data
            else: 
                st.image(img_data, width=w)
                return True
    except: 
        return None

# --- DATA LOADER ---
def load_data():
    if os.path.exists("content.json"):
        with open("content.json", "r") as f: 
            return json.load(f)
    return {}
ALL_DATA = load_data()

# --- STATE ---
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
            st.session_state.update({"set_idx": st.session_state.set_idx + 1, "sub_idx": 0, "phase": "familiarity"})
        else:
            if st.session_state.mastery_count >= len(curr_data) and g_idx < len(all_grades)-1:
                st.session_state.update({"p_grade": all_grades[g_idx+1], "set_idx": 0, "sub_idx": 0, "mastery_count": 0, "phase": "familiarity", "bottleneck_active": True})
                st.toast("Leveling up!", icon="🚀")
            else: 
                st.session_state.step = "summary"
    else:
        sec_qs = curr_data[st.session_state.set_idx]['questions']
        if st.session_state.sub_idx < len(sec_qs)-1: 
            st.session_state.sub_idx += 1
        elif st.session_state.set_idx < len(curr_data)-1: 
            st.session_state.update({"set_idx": st.session_state.set_idx + 1, "sub_idx": 0, "phase": "familiarity"})
        else:
            if st.session_state.perfect_score and g_idx < len(all_grades)-1:
                st.session_state.update({"p_grade": all_grades[g_idx+1], "set_idx": 0, "sub_idx": 0, "phase": "familiarity", "perfect_score": True, "bottleneck_active": True})
                st.toast("Leveling up!", icon="📚")
            else: 
                st.session_state.step = "summary"
    st.rerun()

# --- UI ---
page = st.sidebar.radio("Navigation", ["Take Assessment", "Admin Dashboard"])

if page == "Admin Dashboard":
    st.title("📊 Admin Dashboard")
    if not st.session_state.admin_authenticated:
        pwd = st.text_input("Password", type="password")
        if st.button("Unlock"):
            if pwd == ADMIN_PASSWORD: 
                st.session_state.admin_authenticated = True
                st.rerun()
            else: 
                st.error("Wrong")
    else:
        if st.sidebar.button("Logout"): 
            st.session_state.admin_authenticated = False
            st.rerun()
        res = supabase.table("assessment_results").select("*").order("created_at", desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df['label'] = df['student'] + " | " + df['subject'] + " (" + df['created_at'].str[:16] + ")"
            st.dataframe(df[['created_at', 'student', 'subject', 'grade']], use_container_width=True)
            sel = st.selectbox("Select Record:", df['label'].tolist())
            row = df[df['label'] == sel].iloc[0].to_dict()
            
            st.subheader("📥 Export Documents")
            c1, c2, c3 = st.columns(3)
            c1.download_button("📝 Detailed Log (Internal)", create_detailed_pdf(row), f"Log_{row['student']}.pdf")
            c2.download_button("🎨 Parent Diagnostic (Styled)", create_parent_report_pdf(row), f"Diagnostic_{row['student']}.pdf")
            c3.download_button("🛤️ Learning Path (Landscape)", create_learning_path_pdf(row), f"Path_{row['student']}.pdf")
            
            st.divider()
            v1, v2 = st.columns([1, 2])
            with v1: 
                st.subheader("Internal Logs")
                st.text(row['results'])
                st.subheader("Notes")
                st.write(row['feedback'])
            with v2: 
                st.subheader("AI Analysis")
                st.markdown(row['ai_plan'])

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
                s_grade = st.selectbox("Grade", grades)
        t_tutor = st.text_input("Tutor")
        t_student = st.text_input("Student")
        if st.button("Begin"):
            if t_tutor and t_student and s_grade: 
                st.session_state.update({"p_tutor": t_tutor, "p_student": t_student, "p_subject": s_subj, "p_curr": s_curr, "p_grade": s_grade, "p_start_grade": s_grade, "step": "testing"})
                st.rerun()

    elif st.session_state.step == "testing":
        subj, grade = st.session_state.p_subject, st.session_state.p_grade
        content = ALL_DATA[subj][st.session_state.p_curr][grade]
        curr_set = content[st.session_state.set_idx]
        st.title(f"{subj}: {grade}")
        st.divider()
        if st.session_state.phase == "familiarity":
            topic_lbl = curr_set.get('topic') or curr_set.get('section_title')
            st.header(topic_lbl)
            st.subheader("Is student familiar?")
            if st.button("Yes"): 
                st.session_state.phase = "content"
                st.rerun()
            if st.button("No"):
                record(subj, grade, topic_lbl, "Familiarity", "No")
                st.session_state.perfect_score = False
                if st.session_state.bottleneck_active: 
                    st.session_state.step = "summary"
                else: 
                    advance_logic()
                st.rerun()
        elif st.session_state.phase in ["content", "mastery_retry", "subs"]:
            if subj == "Mathematics":
                if st.session_state.phase in ["content", "mastery_retry"]:
                    lbl = "Mastery" if st.session_state.phase == "content" else "Retry"
                    st.info(curr_set['mastery_q'])
                    display_img(curr_set.get('image') or curr_set.get('mastery_image'))
                    if st.button("✅ Correct"): 
                        record(subj, grade, curr_set['topic'], lbl, "Correct")
                        st.session_state.mastery_count += 1
                        advance_logic()
                    if st.button("❌ Incorrect"):
                        record(subj, grade, curr_set['topic'], lbl, "Incorrect")
                        st.session_state.perfect_score = False
                        if st.session_state.bottleneck_active or st.session_state.phase == "mastery_retry": 
                            st.session_state.step = "summary"
                        else: 
                            st.session_state.update({"phase": "subs", "sub_idx": 0})
                        st.rerun()
                elif st.session_state.phase == "subs":
                    sub = curr_set['subs'][st.session_state.sub_idx]
                    st.subheader(f"Sub-Q {st.session_state.sub_idx+1}")
                    st.write(sub['q'])
                    display_img(sub.get('image'))
                    if st.button("✅ Correct"):
                        record(subj, grade, curr_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Correct")
                        if st.session_state.sub_idx < len(curr_set['subs'])-1: 
                            st.session_state.sub_idx += 1
                        else: 
                            st.session_state.phase = "mastery_retry"
                        st.rerun()
                    if st.button("❌ Incorrect"):
                        record(subj, grade, curr_set['topic'], f"Sub-{st.session_state.sub_idx+1}", "Incorrect")
                        st.session_state.perfect_score = False
                        if st.session_state.bottleneck_active: 
                            st.session_state.step = "summary"
                        else: 
                            advance_logic()
                        st.rerun()
            else: # English
                st.info(curr_set['instruction'])
                if curr_set.get('content_text'):
                    st.code(curr_set['content_text'], language=None)
                display_img(curr_set.get('image') or curr_set.get('mastery_image'))
                q = curr_set['questions'][st.session_state.sub_idx]
                st.subheader(q['q'])
                imgs = q.get('images') or []
                if isinstance(imgs, list) and imgs:
                    cols = st.columns(len(imgs))
                    for i, u in enumerate(imgs):
                        b = display_img(u, True)
                        if b: 
                            cols[i].image(b, use_container_width=True)
                elif q.get('image'): 
                    display_img(q.get('image'))
                if st.button("✅ Correct"): 
                    record(subj, grade, curr_set['section_title'], f"Q{st.session_state.sub_idx+1}", "Correct")
                    advance_logic()
                if st.button("❌ Incorrect"):
                    record(subj, grade, curr_set['section_title'], f"Q{st.session_state.sub_idx+1}", "Incorrect")
                    st.session_state.perfect_score = False
                    if st.session_state.bottleneck_active: 
                        st.session_state.step = "summary"
                    else: 
                        advance_logic()
                    st.rerun()
    elif st.session_state.step == "summary":
        st.title("Summary")
        df = pd.DataFrame(st.session_state.results)
        st.table(df)
        obs = st.text_area("Tutor Feedback")
        if st.button("✨ Generate AI Plan"):
            st.session_state.ai_report = generate_ai_report(st.session_state.p_tutor, st.session_state.p_student, st.session_state.p_subject, st.session_state.p_grade, st.session_state.p_curr, df.to_string(), obs)
            st.markdown(st.session_state.ai_report)
        if st.button("💾 Save"):
            payload = {"tutor": st.session_state.p_tutor, "student": st.session_state.p_student, "subject": st.session_state.p_subject, "curriculum": st.session_state.p_curr, "grade": st.session_state.p_grade, "results": df.to_string(), "feedback": obs, "ai_plan": st.session_state.ai_report}
            supabase.table("assessment_results").insert(payload).execute()
            st.success("Saved!")
        if st.button("🔄 New"): 
            st.session_state.clear()
            st.rerun()
