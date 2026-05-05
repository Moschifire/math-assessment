import streamlit as st
import pandas as pd
import requests
import json

# --- CONFIG ---
# PASTE YOUR GOOGLE APPS SCRIPT URL HERE
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxFm533cRPJWr3e-XBb0iHWoTJhKi0eERBGxXCJ_rkpMJP1fIyKPh4VmU2xE2F1aTr51g/exec" 

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
            "mastery_q": "Look at the numbers 7 and 3. Which is greater and why?",
            "mastery_hint": "Final Hint: Imagine 7 cookies and 3 cookies. Which plate has more?",
            "subs": [
                {"q": "Sub-1: Group A has 4 stars, Group B has 6. How many in each?", "h": "Count carefully."},
                {"q": "Sub-2: If stars hold hands, which group has extras?", "h": "Match 1-to-1."},
                {"q": "Sub-3: Which is bigger: 4 or 6?", "h": "Which comes later when counting?"}
            ]
        },
        {
            "topic": "Composition & Base Ten",
            "mastery_q": "Look at the number 15. Show me how this is one ten and some ones.",
            "mastery_hint": "Final Hint: 15 = 10 + ___.",
            "subs": [
                {"q": "Sub-1: Circle 10 out of 13 circles. How many are left?", "h": "Count ten first."},
                {"q": "Sub-2: If you have 10 and 3, how many total?", "h": "10... 11, 12, 13."},
                {"q": "Sub-3: Write 'thirteen' using digits.", "h": "Starts with 1."}
            ]
        },
        {
            "topic": "Decomposition",
            "mastery_q": "10 apples total. 4 in red bag. How many in blue?",
            "mastery_hint": "Final Hint: 10 - 4 = ___.",
            "subs": [
                {"q": "Sub-1: 5 fingers up, tuck 2. How many left?", "h": "Try it."},
                {"q": "Sub-2: 10-frame has 8 spots filled. How many empty?", "h": "Count empty spots."},
                {"q": "Sub-3: What plus 9 equals 10?", "h": "One jump."}
            ]
        },
        {
            "topic": "Geometry",
            "mastery_q": "I am solid (3D), have 6 square faces, and sit beside a cylinder. What am I?",
            "mastery_hint": "Final Hint: Think of a dice.",
            "subs": [
                {"q": "Sub-1: Which shape has 3 sides and 3 corners?", "h": "Triangle."},
                {"q": "Sub-2: Point to the shape 'above' the square.", "h": "Higher up."},
                {"q": "Sub-3: Is a ball 2D or 3D?", "h": "Can you hold it?"}
            ]
        }
    ],
    "Grade 1": [
        {
            "topic": "Addition (3 Numbers)",
            "mastery_q": "Sam has 8 blue, 4 red, and 2 yellow blocks. Total?",
            "mastery_hint": "Hint: 8 + 2 = 10, then add 4.",
            "subs": [
                {"q": "Sub-1: 8 + 2?", "h": "Make 10."},
                {"q": "Sub-2: 10 + 4?", "h": "One ten, four ones."},
                {"q": "Sub-3: Easiest way to solve 8+4+2?", "h": "Group the numbers that make 10."}
            ]
        },
        {
            "topic": "Place Value",
            "mastery_q": "What is 43 + 10?",
            "mastery_hint": "Hint: Add one ten to the tens place.",
            "subs": [
                {"q": "Sub-1: Tens digit in 43?", "h": "The left digit."},
                {"q": "Sub-2: Ones digit in 43?", "h": "The right digit."},
                {"q": "Sub-3: 10 more than 40?", "h": "10, 20, 30, 40..."}
            ]
        },
        {
            "topic": "Comparing 2-Digit",
            "mastery_q": "Which is true? (A) 42>51, (B) 38<35, (C) 67>63",
            "mastery_hint": "Hint: Compare tens, then ones.",
            "subs": [
                {"q": "Sub-1: More tens: 52 or 25?", "h": "Check first digit."},
                {"q": "Sub-2: What does > mean?", "h": "Greater than."},
                {"q": "Sub-3: 15 < ___?", "h": "Pick a bigger number."}
            ]
        },
        {
            "topic": "Time",
            "mastery_q": "Short hand between 7 and 8. Long hand on 6. Time?",
            "mastery_hint": "Hint: Half past 7.",
            "subs": [
                {"q": "Sub-1: Which hand is shorter?", "h": "Hour hand."},
                {"q": "Sub-2: Long hand on 12 means?", "h": "O'clock."},
                {"q": "Sub-3: Long hand on 6 means?", "h": "Half past."}
            ]
        },
        {
            "topic": "Geometry - Partitioning",
            "mastery_q": "Fold a square in half, then half again. Name the 4 parts.",
            "mastery_hint": "Hint: Fourths.",
            "subs": [
                {"q": "Sub-1: Must equal shares be same size?", "h": "Yes."},
                {"q": "Sub-2: Half of a circle name?", "h": "One half."},
                {"q": "Sub-3: How many shares in a quarter?", "h": "4."}
            ]
        }
    ],
    "Grade 2": [
        {
            "topic": "Place Value to 1,000",
            "mastery_q": "5 hundreds, 16 tens, 2 ones. What number?",
            "mastery_hint": "Hint: 500 + 160 + 2.",
            "subs": [
                {"q": "Sub-1: Tens digit in 706?", "h": "Middle digit."},
                {"q": "Sub-2: Value of 8 in 853?", "h": "800."},
                {"q": "Sub-3: 432 in expanded form?", "h": "400 + 30 + 2."}
            ]
        },
        {
            "topic": "Multi-Step Math",
            "mastery_q": "Baker made 80 muffins. Sold 25, then 30. Left?",
            "mastery_hint": "Hint: 80 - 55.",
            "subs": [
                {"q": "Sub-1: 35 + 12 birds?", "h": "Add."},
                {"q": "Sub-2: 47 - 20 birds?", "h": "Subtract."},
                {"q": "Sub-3: 'How many more needed' operation?", "h": "Subtraction."}
            ]
        },
        {
            "topic": "Measuring",
            "mastery_q": "Desk 45in, Bookshelf 2ft. How much longer is desk?",
            "mastery_hint": "Hint: 2ft = 24in.",
            "subs": [
                {"q": "Sub-1: Tool for a bus?", "h": "Measuring Tape."},
                {"q": "Sub-2: 15in vs 9in difference?", "h": "15 - 9."},
                {"q": "Sub-3: Two 10cm pencils total?", "h": "10 + 10."}
            ]
        },
        {
            "topic": "Time and Money",
            "mastery_q": "Eraser 55c. You have 2 quarters, 2 nickels. Enough?",
            "mastery_hint": "Hint: 50c + 10c = 60c.",
            "subs": [
                {"q": "Sub-1: Value of a quarter?", "h": "25c."},
                {"q": "Sub-2: 2 quarters + 1 dime total?", "h": "60c."},
                {"q": "Sub-3: Minute hand at 8?", "h": "40 mins."}
            ]
        },
        {
            "topic": "Geometry and Arrays",
            "mastery_q": "Partition rectangle into 4 rows and 3 columns. Total?",
            "mastery_hint": "Hint: 4 x 3.",
            "subs": [
                {"q": "Sub-1: Rows go?", "h": "Across."},
                {"q": "Sub-2: 3 rows, 4 columns?", "h": "12."},
                {"q": "Sub-3: 2 rows, 5 columns addition?", "h": "5+5."}
            ]
        }
    ]
}

# --- INITIALIZE PERMANENT STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.perm_grade = "Kindergarten"
    st.session_state.perm_tutor = ""
    st.session_state.perm_student = ""
    st.session_state.perm_curriculum = "US Common Core"
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    st.session_state.phase = "familiarity"
    st.session_state.results = []
    st.session_state.mastery_streak = 0
    st.session_state.bottleneck = False

def record_entry(topic, detail, status, hint):
    st.session_state.results.append({
        "Grade": st.session_state.perm_grade,
        "Topic": topic,
        "Detail": detail,
        "Status": status,
        "Hint Used": "Yes" if hint else "No"
    })

# --- UI LOGIC ---
if st.session_state.step == "setup":
    st.title("Math Diagnostic: Setup")
    # Store temporary widget values
    t_tutor = st.text_input("Tutor Name")
    t_student = st.text_input("Student Name")
    t_curr = st.selectbox("Curriculum", ["US Common Core", "UK National", "IB"])
    t_grade = st.selectbox("Starting Class", ["Kindergarten", "Grade 1", "Grade 2"])
    
    if st.button("Start Assessment"):
        if t_tutor and t_student:
            # CAPTURE into permanent session state before switching screens
            st.session_state.perm_tutor = t_tutor
            st.session_state.perm_student = t_student
            st.session_state.perm_curriculum = t_curr
            st.session_state.perm_grade = t_grade
            st.session_state.step = "testing"
            st.rerun()
        else:
            st.error("Please provide both names.")

elif st.session_state.step == "testing":
    # Safely access content using captured perm_grade
    current_grade = st.session_state.perm_grade
    data = ASSESSMENT_CONTENT[current_grade][st.session_state.set_idx]
    
    st.title(f"Diagnostic: {current_grade}")
    st.caption(f"Tutor: {st.session_state.perm_tutor} | Student: {st.session_state.perm_student}")

    if st.session_state.phase == "familiarity":
        st.subheader(f"Topic: {data['topic']}")
        st.write("Is the student familiar with this topic?")
        c1, c2 = st.columns(2)
        if c1.button("Yes"):
            st.session_state.phase = "mastery"
            st.rerun()
        if c2.button("No, skip"):
            record_entry(data['topic'], "Familiarity", "Not Familiar", False)
            st.session_state.bottleneck = True
            if st.session_state.set_idx < 4:
                st.session_state.set_idx += 1
            else:
                st.session_state.step = "summary"
            st.rerun()

    elif st.session_state.phase == "mastery":
        st.info(f"**MASTERY QUESTION:** {data['mastery_q']}")
        h = st.checkbox("Show Hint?")
        if h: st.warning(data['mastery_hint'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(data['topic'], "Mastery Q", "Correct", h)
            st.session_state.mastery_streak += 1
            if st.session_state.set_idx < 4:
                st.session_state.set_idx += 1
                st.session_state.phase = "familiarity"
            else:
                # End of Grade Logic
                if st.session_state.mastery_streak == 5 and not st.session_state.bottleneck:
                    grades = list(ASSESSMENT_CONTENT.keys())
                    idx = grades.index(current_grade)
                    if idx < len(grades)-1:
                        st.session_state.perm_grade = grades[idx+1]
                        st.session_state.set_idx = 0
                        st.session_state.mastery_streak = 0
                        st.session_state.phase = "familiarity"
                        st.success("Perfect score! Advancing...")
                    else: st.session_state.step = "summary"
                else: st.session_state.step = "summary"
            st.rerun()
            
        if c2.button("❌ Incorrect"):
            record_entry(data['topic'], "Mastery Q", "Incorrect", h)
            st.session_state.bottleneck = True
            st.session_state.phase = "subs"
            st.session_state.sub_idx = 0
            st.rerun()

    elif st.session_state.phase == "subs":
        sub = data['subs'][st.session_state.sub_idx]
        st.write(f"**Sub-Question {st.session_state.sub_idx + 1}:**")
        st.info(sub['q'])
        h = st.checkbox(f"Hint?")
        if h: st.warning(sub['h'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct/Next"):
            record_entry(data['topic'], f"Sub {st.session_state.sub_idx+1}", "Correct", h)
            if st.session_state.sub_idx < 2: 
                st.session_state.sub_idx += 1
            else:
                if st.session_state.set_idx < 4:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()
        if c2.button("❌ Incorrect"):
            record_entry(data['topic'], f"Sub {st.session_state.sub_idx+1}", "Incorrect", h)
            if st.session_state.sub_idx < 2: 
                st.session_state.sub_idx += 1
            else:
                if st.session_state.set_idx < 4:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()

elif st.session_state.step == "summary":
    st.header("Assessment Complete")
    df = pd.DataFrame(st.session_state.results)
    st.table(df)
    
    # Format report
    report_text = ""
    for r in st.session_state.results:
        report_text += f"[{r['Grade']}] {r['Topic']} - {r['Status']} (Hint: {r['Hint Used']})\n"

    if st.button("Submit to Google Sheets"):
        payload = {
            "tutor": st.session_state.perm_tutor,
            "student": st.session_state.perm_student,
            "curriculum": st.session_state.perm_curriculum,
            "grade": st.session_state.perm_grade,
            "results": report_text
        }
        try:
            requests.post(WEBHOOK_URL, data=json.dumps(payload))
            st.success("Successfully Submitted!")
        except:
            st.error("Submission failed. Check your Webhook URL.")
