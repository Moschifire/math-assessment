import streamlit as st
import pandas as pd
import requests
import json

# --- CONFIG ---
# PASTE YOUR GOOGLE APPS SCRIPT URL HERE
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwuerNR456dU0l1v2Zs4XOexp1xOpgomdM3JXOgM-tqkAKtijqehy7Z1745VXRBDRNm/exec" 

st.set_page_config(page_title="Math Diagnostic Assessment", layout="centered")

# --- DATA: THE QUESTIONS ---
ASSESSMENT_CONTENT = {
    "Kindergarten": [
        {
            "topic": "Cardinality and Addition",
            "mastery_q": "There are 3 red apples and 2 green apples. How many apples are there in all? Tell me or draw a picture to show how you found the answer.",
            "mastery_hint": "Final Hint: You can count all the apples starting from 1, or start at 3 and count two more.",
            "subs": [
                {"q": "Sub-Question 1: Here is a group of red apples: 🍎 🍎 🍎. Point to each one as you count them. How many are there?", "h": "Hint: Use your finger to touch each apple as you say the numbers '1, 2...'"},
                {"q": "Sub-Question 2: Here is a group of green apples: 🍏 🍏. How many green apples are there?", "h": "Hint: Count them just like you did the red ones."},
                {"q": "Sub-Question 3: If we put the red apples and green apples in one big basket, what is the next number you say after '3' to keep counting?", "h": "Hint: Start at 3 (the red ones) and count on: '3... 4...'"}
            ]
        },
        {
            "topic": "Comparing Numbers",
            "mastery_q": "Look at the numbers 7 and 3. Tell me which number is greater than the other and explain how you know.",
            "mastery_hint": "Final Hint: Imagine 7 cookies and 3 cookies. Which plate has more?",
            "subs": [
                {"q": "Sub-Question 1: Group A has 4 stars (⭐) and Group B has 6 stars (⭐). How many are in each group?", "h": "Hint: Count each group carefully and remember the last number you say."},
                {"q": "Sub-Question 2: If every star in Group A holds hands with a star in Group B, will there be stars left over in Group B?", "h": "Hint: Draw a line from one star in A to one star in B. See which group has extra."},
                {"q": "Sub-Question 3: Which number is bigger when we count: 4 or 6?", "h": "Hint: Think about which number comes later when you count to 10."}
            ]
        },
        {
            "topic": "Composition & Base Ten",
            "mastery_q": "Look at the number 15. Use blocks or a drawing to show me how this number is made of one group of ten and some extra ones. How many extra ones are there?",
            "mastery_hint": "Final Hint: 15 is the same as 10+___.",
            "subs": [
                {"q": "Sub-Question 1: Use these circles: ⚪. Circle a group of exactly 10. How many are left outside your circle? (Provide 13 circles).", "h": "Hint: Count out ten circles first and draw a big ring around them."},
                {"q": "Sub-Question 2: If you have 10 circles in a ring and 3 circles outside, how many are there altogether?", "h": "Hint: Count on from ten: '10... 11, 12, 13.'"},
                {"q": "Sub-Question 3: How do you write the number 'thirteen' using digits?", "h": "Hint: It has a '1' for the group of ten and a '3' for the extra ones."}
            ]
        },
        {
            "topic": "Decomposition",
            "mastery_q": "You have 10 apples total. Some are in a red bag and some are in a blue bag. If 4 apples are in the red bag, how many must be in the blue bag? Show your work.",
            "mastery_hint": "Final Hint: Start with 10 fingers or 10 circles. Take away 4. What is left?",
            "subs": [
                {"q": "Sub-Question 1: I have 5 fingers held up. If I tuck 2 fingers down, how many are still up?", "h": "Hint: Look at your hand and try it!"},
                {"q": "Sub-Question 2: If we have 10 spots on a tens-frame and 8 are filled, how many are empty?", "h": "Hint: Count the empty boxes in the frame."},
                {"q": "Sub-Question 3: What number do you need to add to 9 to make 10?", "h": "Hint: If you have 9, how many more jumps to get to 10?"}
            ]
        },
        {
            "topic": "Geometry and Position",
            "mastery_q": "I am a shape. I am solid (3D), I have 6 flat faces that are all squares, and I am sitting beside a cylinder. What shape am I?",
            "mastery_hint": "Final Hint: Think of a toy block or a dice.",
            "subs": [
                {"q": "Sub-Question 1: Look at these shapes. Which one has 3 sides and 3 corners?", "h": "Hint: It looks like a slice of pie or a mountain."},
                {"q": "Sub-Question 2: Point to the shape that is above the square.", "h": "Hint: 'Above' means higher up, like the sun is above the trees."},
                {"q": "Sub-Question 3: Is a ball a 'flat' shape (2D) or a 'solid' shape (3D)?", "h": "Hint: Can you hold it in your hand, or is it just a drawing on paper?"}
            ]
        }
    ],
    "Grade 1": [
        {
            "topic": "Addition with Three Numbers",
            "mastery_q": "Sam has 8 blue blocks, 4 red blocks, and 2 yellow blocks. How many blocks does he have in all?",
            "mastery_hint": "Final Hint: Add the 8 and 2 together first to make a ten, then add the 4.",
            "subs": [
                {"q": "Sub-1: What is 8+2?", "h": "Hint: Use fingers or number line."},
                {"q": "Sub-2: What is 10+4?", "h": "Hint: One bundle of ten and four extra ones."},
                {"q": "Sub-3: Which is easiest: (A) 8+4, (B) 4+2, (C) 8+2", "h": "Hint: Look for numbers that make 10."}
            ]
        },
        {
            "topic": "Place Value - Tens and Ones",
            "mastery_q": "What is 43 + 10?",
            "mastery_hint": "Final Hint: Add one more ten to the tens place.",
            "subs": [
                {"q": "Sub-1: In 43, which digit is in the tens place?", "h": "Hint: First digit on the left."},
                {"q": "Sub-2: How many ones are in the number 43?", "h": "Hint: The digit on the right."},
                {"q": "Sub-3: What is 10 more than 40?", "h": "Hint: Count up by tens."}
            ]
        },
        {
            "topic": "Comparing Two-Digit Numbers",
            "mastery_q": "Which math sentence is correct? (A) 42>51, (B) 38<35, (C) 67>63, (D) 21=12",
            "mastery_hint": "Final Hint: First look at the tens, then the ones.",
            "subs": [
                {"q": "Sub-1: Which has more tens: 52 or 25?", "h": "Hint: Look at the first digit."},
                {"q": "Sub-2: What does > mean?", "h": "Hint: Mouth opens to the bigger number."},
                {"q": "Sub-3: Which makes this true: 15 < ___? (10, 15, or 20)", "h": "Hint: Need a bigger number."}
            ]
        },
        {
            "topic": "Telling Time",
            "mastery_q": "Short hand between 7 and 8. Long hand on 6. What time?",
            "mastery_hint": "Final Hint: Halfway past 7.",
            "subs": [
                {"q": "Sub-1: Which hand is shorter?", "h": "Hint: Shorter hand is the hour."},
                {"q": "Sub-2: Long hand on 12 means...", "h": "Hint: O'clock."},
                {"q": "Sub-3: Long hand on 6 means...", "h": "Hint: Half past."}
            ]
        },
        {
            "topic": "Geometry - Partitioning",
            "mastery_q": "Fold a square in half, then half again. What are the 4 shapes called?",
            "mastery_hint": "Final Hint: Think of 4 equal pieces.",
            "subs": [
                {"q": "Sub-1: If one part is much bigger, are they equal?", "h": "Hint: Must be same size."},
                {"q": "Sub-2: Divide a circle into 2 equal shares. Name?", "h": "Hint: One half."},
                {"q": "Sub-3: How many shares in a quarter?", "h": "Hint: Like wheels on a car."}
            ]
        }
    ],
    "Grade 2": [
        {
            "topic": "Place Value to 1,000",
            "mastery_q": "I have 5 hundreds, 16 tens, and 2 ones. What number am I?",
            "mastery_hint": "Final Hint: 500 + 160 + 2.",
            "subs": [
                {"q": "Sub-1: In 706, what is in the tens place?", "h": "Hint: Middle digit."},
                {"q": "Sub-2: Value of 8 in 853?", "h": "Hint: Hundreds place."},
                {"q": "Sub-3: 432 in expanded form?", "h": "Hint: 400 + 30 + 2"}
            ]
        },
        {
            "topic": "Multi-Step Math",
            "mastery_q": "Made 80 muffins. Sold 25, then sold 30. Left?",
            "mastery_hint": "Final Hint: 80 - (25 + 30).",
            "subs": [
                {"q": "Sub-1: 35 birds + 12 more. Total?", "h": "Hint: Addition."},
                {"q": "Sub-2: 47 birds - 20 fly away. Left?", "h": "Hint: Subtraction."},
                {"q": "Sub-3: 'How many more are needed' means what?", "h": "Hint: Finding the gap."}
            ]
        },
        {
            "topic": "Measuring",
            "mastery_q": "Desk is 45in. Bookshelf is 2ft. How much longer is desk? (1ft=12in)",
            "mastery_hint": "Final Hint: 45 minus 24.",
            "subs": [
                {"q": "Sub-1: Tool for a bus?", "h": "Hint: Measuring Tape."},
                {"q": "Sub-2: Line A (15) vs Line B (9). Diff?", "h": "Hint: 15 - 9."},
                {"q": "Sub-3: Two 10cm pencils end-to-end?", "h": "Hint: 10 + 10."}
            ]
        },
        {
            "topic": "Time and Money",
            "mastery_q": "Eraser costs 55¢. You have 2 quarters and 2 nickels. Enough?",
            "mastery_hint": "Final Hint: 50 + 10 = 60¢.",
            "subs": [
                {"q": "Sub-1: Value of one quarter?", "h": "Hint: 25¢."},
                {"q": "Sub-2: 2 quarters + 1 dime total?", "h": "Hint: 25+25+10."},
                {"q": "Sub-3: Minute hand on 8 means how many mins?", "h": "Hint: Count by 5s."}
            ]
        },
        {
            "topic": "Geometry and Arrays",
            "mastery_q": "Partition rectangle into 4 rows and 3 columns. Total?",
            "mastery_hint": "Final Hint: 4 x 3.",
            "subs": [
                {"q": "Sub-1: Do rows go across or up/down?", "h": "Hint: Movie theater seats."},
                {"q": "Sub-2: 3 rows, 4 columns. Total?", "h": "Hint: Count them."},
                {"q": "Sub-3: 2 rows, 5 columns. Which works? (A) 5+5, (B) 2+2+2+2+2, (C) Both", "h": "Hint: Rows or columns."}
            ]
        }
    ]
}

# --- SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.grade = "Kindergarten"
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    st.session_state.phase = "familiarity"
    st.session_state.results = []
    st.session_state.mastery_streak = 0
    st.session_state.bottleneck = False

def record_entry(topic, detail, status, hint):
    st.session_state.results.append({
        "Grade": st.session_state.grade,
        "Topic": topic,
        "Detail": detail,
        "Status": status,
        "Hint Used": "Yes" if hint else "No"
    })

# --- UI ---
st.title("Math Diagnostic Pro")

if st.session_state.step == "setup":
    st.session_state.tutor = st.text_input("Tutor Name")
    st.session_state.student = st.text_input("Student Name")
    st.session_state.grade = st.selectbox("Starting Class", ["Kindergarten", "Grade 1", "Grade 2"])
    if st.button("Start Assessment"):
        if st.session_state.tutor and st.session_state.student:
            st.session_state.step = "testing"
            st.rerun()

elif st.session_state.step == "testing":
    data = ASSESSMENT_CONTENT[st.session_state.grade][st.session_state.set_idx]
    st.caption(f"Student: {st.session_state.student} | Grade: {st.session_state.grade}")
    
    if st.session_state.phase == "familiarity":
        st.subheader(f"Topic: {data['topic']}")
        st.write("Is the student familiar with this topic?")
        col1, col2 = st.columns(2)
        if col1.button("Yes, proceed"):
            st.session_state.phase = "mastery"
            st.rerun()
        if col2.button("No, skip set"):
            record_entry(data['topic'], "Familiarity", "Not Familiar", False)
            st.session_state.bottleneck = True
            if st.session_state.set_idx < 4:
                st.session_state.set_idx += 1
            else: st.session_state.step = "summary"
            st.rerun()

    elif st.session_state.phase == "mastery":
        st.info(f"**MASTERY QUESTION:** {data['mastery_q']}")
        h_used = st.checkbox("Student needs hint?")
        if h_used: st.warning(data['mastery_hint'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(data['topic'], "Mastery Q", "Correct", h_used)
            st.session_state.mastery_streak += 1
            if st.session_state.set_idx < 4:
                st.session_state.set_idx += 1
                st.session_state.phase = "familiarity"
            else:
                # End of current grade check
                if st.session_state.mastery_streak == 5 and not st.session_state.bottleneck:
                    grades = list(ASSESSMENT_CONTENT.keys())
                    g_idx = grades.index(st.session_state.grade)
                    if g_idx < len(grades)-1:
                        st.session_state.grade = grades[g_idx+1]
                        st.session_state.set_idx = 0
                        st.session_state.mastery_streak = 0
                        st.session_state.phase = "familiarity"
                        st.success("Advanced to next grade!")
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
        h_used = st.checkbox("Use hint?")
        if h_used: st.warning(sub_data['h'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Next/Correct"):
            record_entry(data['topic'], f"Sub {st.session_state.sub_idx+1}", "Correct", h_used)
            if st.session_state.sub_idx < 2: st.session_state.sub_idx += 1
            else:
                if st.session_state.set_idx < 4:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()
        if c2.button("❌ Incorrect"):
            record_entry(data['topic'], f"Sub {st.session_state.sub_idx+1}", "Incorrect", h_used)
            if st.session_state.sub_idx < 2: st.session_state.sub_idx += 1
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
    
    if st.button("Submit Results"):
        payload = {
            "tutor": st.session_state.tutor,
            "student": st.session_state.student,
            "data": df.to_json()
        }
        try:
            requests.post(WEBHOOK_URL, data=json.dumps(payload))
            st.success("Sent to Google Sheets!")
        except:
            st.error("Submission failed. Check Webhook URL.")
