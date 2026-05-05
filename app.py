import streamlit as st
import pandas as pd
import requests
import json

# --- CONFIG ---
# IMPORTANT: Ensure you have pasted your Google Web App URL here
WEBHOOK_URL = "https://script.google.com/macros/s/XXXX/exec" 

st.set_page_config(page_title="Math Diagnostic Pro", layout="centered")

# --- DATA: THE QUESTIONS ---
ASSESSMENT_CONTENT = {
    "Kindergarten": [
        {
            "topic": "Cardinality and Addition",
            "mastery_q": "There are 3 red apples and 2 green apples. How many apples are there in all?",
            "mastery_hint": "Final Hint: You can count all the apples starting from 1, or start at 3 and count two more.",
            "subs": [
                {"q": "Sub-1: Here is a group of red apples: 🍎 🍎 🍎. How many are there?", "h": "Hint: Touch each apple as you count."},
                {"q": "Sub-2: Here is a group of green apples: 🍏 🍏. How many are there?", "h": "Hint: Count them just like the red ones."},
                {"q": "Sub-3: After 3 red apples, what is the next number to keep counting?", "h": "Hint: 3... 4..."}
            ]
        },
        {
            "topic": "Comparing Numbers",
            "mastery_q": "Which is greater: 7 or 3? Explain how you know.",
            "mastery_hint": "Final Hint: Imagine 7 cookies and 3 cookies. Which plate has more?",
            "subs": [
                {"q": "Sub-1: Count Group A (4 stars) and Group B (6 stars).", "h": "Count carefully."},
                {"q": "Sub-2: If they hold hands, which group has stars left over?", "h": "Draw lines between them."},
                {"q": "Sub-3: Which number comes later when counting: 4 or 6?", "h": "1, 2, 3, 4, 5, 6..."}
            ]
        },
        {
            "topic": "Composition & Base Ten",
            "mastery_q": "Look at the number 15. How many tens and how many extra ones are there?",
            "mastery_hint": "Final Hint: 15 is 10 + ___.",
            "subs": [
                {"q": "Sub-1: Circle a group of 10 circles out of 13. How many left?", "h": "Count 10 first."},
                {"q": "Sub-2: If you have 10 and 3, how many altogether?", "h": "10... 11, 12, 13."},
                {"q": "Sub-3: How do you write 'thirteen'?", "h": "It starts with a 1."}
            ]
        },
        {
            "topic": "Decomposition",
            "mastery_q": "10 apples total. 4 in red bag. How many in blue?",
            "mastery_hint": "Final Hint: 10 take away 4.",
            "subs": [
                {"q": "Sub-1: 5 fingers up, tuck 2. How many left?", "h": "Try it on your hand."},
                {"q": "Sub-2: 10 spots on a frame, 8 filled. How many empty?", "h": "Count empty boxes."},
                {"q": "Sub-3: What do you add to 9 to make 10?", "h": "One jump."}
            ]
        },
        {
            "topic": "Geometry",
            "mastery_q": "I have 6 square faces and am 3D. What am I?",
            "mastery_hint": "Final Hint: Think of a dice.",
            "subs": [
                {"q": "Sub-1: Which shape has 3 sides and 3 corners?", "h": "Looks like a pizza slice."},
                {"q": "Sub-2: Point to the shape above the square.", "h": "Above is higher up."},
                {"q": "Sub-3: Is a ball 2D (flat) or 3D (solid)?", "h": "Can you hold it?"}
            ]
        }
    ],
    "Grade 1": [
        {
            "topic": "Addition (3 Numbers)",
            "mastery_q": "Sam has 8 blue blocks, 4 red blocks, and 2 yellow blocks. How many in all?",
            "mastery_hint": "Hint: 8 + 2 = 10.",
            "subs": [
                {"q": "Sub-1: What is 8+2?", "h": "Use fingers"},
                {"q": "Sub-2: What is 10+4?", "h": "One ten and four ones"},
                {"q": "Sub-3: Easiest way to solve 8+4+2?", "h": "Make 10 first"}
            ]
        },
        {
            "topic": "Place Value",
            "mastery_q": "What is 43 + 10?",
            "mastery_hint": "Hint: Only the tens digit changes.",
            "subs": [
                {"q": "Sub-1: Tens digit in 43?", "h": "Left digit"},
                {"q": "Sub-2: Ones digit in 43?", "h": "Right digit"},
                {"q": "Sub-3: What is 10 more than 40?", "h": "Count by 10s"}
            ]
        },
        {
            "topic": "Comparing 2-Digit",
            "mastery_q": "Which is correct? (A) 42>51, (B) 38<35, (C) 67>63",
            "mastery_hint": "Hint: Look at tens, then ones.",
            "subs": [
                {"q": "Sub-1: More tens: 52 or 25?", "h": "First digit"},
                {"q": "Sub-2: What does > mean?", "h": "Bigger than"},
                {"q": "Sub-3: Which makes this true: 15 < ___?", "h": "Need a bigger number"}
            ]
        },
        {
            "topic": "Time",
            "mastery_q": "Short hand between 7/8, long hand on 6. Time?",
            "mastery_hint": "Hint: Halfway past 7.",
            "subs": [
                {"q": "Sub-1: Which hand is shorter?", "h": "Hour hand"},
                {"q": "Sub-2: Long hand on 12 means?", "h": "O'clock"},
                {"q": "Sub-3: Long hand on 6 means?", "h": "Half past"}
            ]
        },
        {
            "topic": "Partitioning",
            "mastery_q": "Fold a square in half, then half again. Name the 4 parts.",
            "mastery_hint": "Hint: 4 pieces.",
            "subs": [
                {"q": "Sub-1: If different sizes, are they equal?", "h": "No"},
                {"q": "Sub-2: Half of a circle?", "h": "One half"},
                {"q": "Sub-3: Shares in a quarter?", "h": "4"}
            ]
        }
    ],
    "Grade 2": [
        {
            "topic": "PV to 1,000",
            "mastery_q": "5 hundreds, 16 tens, 2 ones. Number?",
            "mastery_hint": "Hint: 500 + 160 + 2.",
            "subs": [
                {"q": "Sub-1: Tens in 706?", "h": "Middle digit"},
                {"q": "Sub-2: Value of 8 in 853?", "h": "Hundreds"},
                {"q": "Sub-3: 432 in expanded form?", "h": "400+30+2"}
            ]
        },
        {
            "topic": "Multi-Step Math",
            "mastery_q": "80 muffins. Sold 25 morning, 30 afternoon. Left?",
            "mastery_hint": "Hint: 80 - (25+30).",
            "subs": [
                {"q": "Sub-1: 35 + 12 birds?", "h": "Addition"},
                {"q": "Sub-2: 47 - 20 birds?", "h": "Subtraction"},
                {"q": "Sub-3: 'How many more' means?", "h": "Gap/Subtraction"}
            ]
        },
        {
            "topic": "Measuring",
            "mastery_q": "Desk 45in, Bookshelf 2ft. Difference in inches?",
            "mastery_hint": "Hint: 2ft = 24in. Subtract.",
            "subs": [
                {"q": "Sub-1: Tool for a bus?", "h": "Tape Measure"},
                {"q": "Sub-2: 15in vs 9in diff?", "h": "Subtract"},
                {"q": "Sub-3: Two 10cm pencils end-to-end?", "h": "Add"}
            ]
        },
        {
            "topic": "Time/Money",
            "mastery_q": "Eraser 55c. Have 2 quarters, 2 nickels. Enough?",
            "mastery_hint": "Hint: Quarters=50c, Nickels=10c. Total=60c.",
            "subs": [
                {"q": "Sub-1: Value of a quarter?", "h": "25c"},
                {"q": "Sub-2: 2 quarters + 1 dime?", "h": "60c"},
                {"q": "Sub-3: Minute hand at 8 means?", "h": "40 mins"}
            ]
        },
        {
            "topic": "Arrays",
            "mastery_q": "Rectangle with 4 rows and 3 columns. Total squares?",
            "mastery_hint": "Hint: 4 x 3.",
            "subs": [
                {"q": "Sub-1: Rows go?", "h": "Across"},
                {"q": "Sub-2: 3 rows, 4 columns?", "h": "12"},
                {"q": "Sub-3: Addition for 2 rows, 5 cols?", "h": "5+5 or 2+2+2+2+2"}
            ]
        }
    ]
}

# --- INITIALIZE STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.current_grade = "Kindergarten"
    st.session_state.curriculum_choice = "US Common Core"
    st.session_state.tutor_name = ""
    st.session_state.student_name = ""
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    st.session_state.phase = "familiarity"
    st.session_state.results = []
    st.session_state.mastery_streak = 0
    st.session_state.bottleneck = False

def record_entry(topic, detail, status, hint):
    st.session_state.results.append({
        "Grade": st.session_state.current_grade,
        "Topic": topic,
        "Detail": detail,
        "Status": status,
        "Hint Used": "Yes" if hint else "No"
    })

# --- UI ---
st.title("Math Diagnostic Pro")

if st.session_state.step == "setup":
    # Using 'key' ensures these variables stay in session_state even when screen changes
    st.text_input("Tutor Name", key="tutor_name")
    st.text_input("Student Name", key="student_name")
    st.selectbox("Curriculum", ["US Common Core", "UK National", "IB"], key="curriculum_choice")
    st.selectbox("Starting Class", ["Kindergarten", "Grade 1", "Grade 2"], key="current_grade")
    
    if st.button("Start Assessment"):
        if st.session_state.tutor_name and st.session_state.student_name:
            st.session_state.step = "testing"
            st.rerun()
        else:
            st.warning("Please enter names to begin.")

elif st.session_state.step == "testing":
    data = ASSESSMENT_CONTENT[st.session_state.current_grade][st.session_state.set_idx]
    st.caption(f"Tutor: {st.session_state.tutor_name} | Student: {st.session_state.student_name} | Grade: {st.session_state.current_grade}")
    
    if st.session_state.phase == "familiarity":
        st.subheader(f"Topic: {data['topic']}")
        st.write("Is the student familiar with this topic?")
        col1, col2 = st.columns(2)
        if col1.button("Yes"):
            st.session_state.phase = "mastery"
            st.rerun()
        if col2.button("No, skip set"):
            record_entry(data['topic'], "Familiarity", "Not Familiar", False)
            st.session_state.bottleneck = True
            if st.session_state.set_idx < 4: 
                st.session_state.set_idx += 1
            else: 
                st.session_state.step = "summary"
            st.rerun()

    elif st.session_state.phase == "mastery":
        st.info(f"**MASTERY QUESTION:** {data['mastery_q']}")
        h_used = st.checkbox("Student used hint?")
        if h_used: st.warning(data['mastery_hint'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(data['topic'], "Mastery Q", "Correct", h_used)
            st.session_state.mastery_streak += 1
            if st.session_state.set_idx < 4:
                st.session_state.set_idx += 1
                st.session_state.phase = "familiarity"
            else:
                # Grade completion logic
                if st.session_state.mastery_streak == 5 and not st.session_state.bottleneck:
                    grades = list(ASSESSMENT_CONTENT.keys())
                    g_idx = grades.index(st.session_state.current_grade)
                    if g_idx < len(grades)-1:
                        st.session_state.current_grade = grades[g_idx+1]
                        st.session_state.set_idx = 0
                        st.session_state.mastery_streak = 0
                        st.session_state.phase = "familiarity"
                        st.success(f"Perfect Mastery! Advancing to {st.session_state.current_grade}")
                    else: st.session_state.step = "summary"
                else: st.session_state.step = "summary"
            st.rerun()
            
        if c2.button("❌ Incorrect"):
            record_entry(data['topic'], "Mastery Q", "Incorrect", h_used)
            st.session_state.bottleneck = True
            st.session_state.phase = "subs"
            st.session_state.sub_idx = 0
            st.rerun()

    elif st.session_state.phase == "subs":
        sub_data = data['subs'][st.session_state.sub_idx]
        st.write(f"**Sub-Question {st.session_state.sub_idx + 1}:**")
        st.info(sub_data['q'])
        h_used = st.checkbox(f"Hint for Sub {st.session_state.sub_idx + 1}?")
        if h_used: st.warning(sub_data['h'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(data['topic'], f"Sub {st.session_state.sub_idx+1}", "Correct", h_used)
            if st.session_state.sub_idx < 2: 
                st.session_state.sub_idx += 1
            else:
                if st.session_state.set_idx < 4:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()
        if c2.button("❌ Incorrect"):
            record_entry(data['topic'], f"Sub {st.session_state.sub_idx+1}", "Incorrect", h_used)
            if st.session_state.sub_idx < 2: 
                st.session_state.sub_idx += 1
            else:
                if st.session_state.set_idx < 4:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()

elif st.session_state.step == "summary":
    st.header("Diagnostic Summary")
    df = pd.DataFrame(st.session_state.results)
    st.dataframe(df)
    
    # Format for Google Sheet
    report_lines = []
    for r in st.session_state.results:
        report_lines.app
