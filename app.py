import streamlit as st
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
                {"q": "Sub-Question 1: What is 8+2?", "h": "Hint: Use your fingers or a number line to count on from 8."},
                {"q": "Sub-Question 2: What is 10+4?", "h": "Hint: Think about one bundle of ten and four extra ones."},
                {"q": "Sub-Question 3: Which is the easiest way to solve 8+4+2? (A) 8+4, (B) 4+2, (C) 8+2", "h": "Hint: Look for two numbers that add up to exactly 10."}
            ]
        },
        {
            "topic": "Place Value - Tens and Ones",
            "mastery_q": "What is 43 + 10?",
            "mastery_hint": "Final Hint: Add one more ten to the tens place, but keep the ones place the same.",
            "subs": [
                {"q": "Sub-Question 1: In the number 43, which digit is in the tens place?", "h": "Hint: The tens place is the first digit on the left."},
                {"q": "Sub-Question 2: How many ones are in the number 43?", "h": "Hint: The ones place is the digit on the right."},
                {"q": "Sub-Question 3: What is 10 more than 40?", "h": "Hint: Count up by tens: 10, 20, 30, 40... what is next?"}
            ]
        },
        {
            "topic": "Comparing Two-Digit Numbers",
            "mastery_q": "Which math sentence is correct? (A) 42>51, (B) 38<35, (C) 67>63, (D) 21=12",
            "mastery_hint": "Final Hint: First look at the tens. If the tens are the same, look at the ones.",
            "subs": [
                {"q": "Sub-Question 1: Which number has more tens: 52 or 25?", "h": "Hint: Look at the first digit of each number."},
                {"q": "Sub-Question 2: What does this symbol mean: >?", "h": "Hint: The 'mouth' opens toward the bigger number."},
                {"q": "Sub-Question 3: Which number makes this true: 15 < ___? (10, 15, or 20)", "h": "Hint: You need a number that is bigger than 15."}
            ]
        },
        {
            "topic": "Telling Time",
            "mastery_q": "The short hand is between the 7 and the 8. The long hand is on the 6. What time is it?",
            "mastery_hint": "Final Hint: It is halfway past the 7. Write the time using a colon (:).",
            "subs": [
                {"q": "Sub-Question 1: On a clock, which hand is shorter: the hour hand or the minute hand?", "h": "Hint: The shorter hand tells us what hour it is."},
                {"q": "Sub-Question 2: When the long minute hand points to the 12, it is...", "h": "Hint: This is the start of a brand new hour (o'clock)."},
                {"q": "Sub-Question 3: When the long minute hand points to the 6, it is...", "h": "Hint: The hand has moved halfway around (half past)."}
            ]
        },
        {
            "topic": "Geometry - Partitioning",
            "mastery_q": "If you take a square and fold it in half, and then fold it in half again, what are the 4 new equal shapes called?",
            "mastery_hint": "Final Hint: 'Fourths' and 'Quarters' mean the shape is split into 4 equal pieces.",
            "subs": [
                {"q": "Sub-Question 1: If one part is much bigger than the other, are they 'equal shares'?", "h": "Hint: Equal shares must be the exact same size."},
                {"q": "Sub-Question 2: If you divide a circle into two equal shares, what is one of those shares called?", "h": "Hint: Think of sharing a cookie between two people."},
                {"q": "Sub-Question 3: How many equal shares are in a 'quarter' of a shape?", "h": "Hint: Same as the number of wheels on a car."}
            ]
        }
    ],
    "Grade 2": [
        {
            "topic": "Place Value to 1,000",
            "mastery_q": "I am a number. I have 5 hundreds, 16 tens, and 2 ones. What number am I in standard form?",
            "mastery_hint": "Final Hint: 500 + 160 + 2.",
            "subs": [
                {"q": "Sub-Question 1: In 706, which digit is in the tens place?", "h": "Hint: Look at the middle digit."},
                {"q": "Sub-Question 2: What is the value of the 8 in 853?", "h": "Hint: It is in the hundreds place."},
                {"q": "Sub-Question 3: Write 432 in expanded form.", "h": "Hint: 400 + 30 + 2"}
            ]
        },
        {
            "topic": "Multi-Step Addition & Subtraction",
            "mastery_q": "A baker made 80 muffins. He sold 25 in the morning and 30 in the afternoon. How many left?",
            "mastery_hint": "Final Hint: Add 25+30 first, then subtract from 80.",
            "subs": [
                {"q": "Sub-Question 1: 35 birds on a tree. 12 more fly there. Total?", "h": "Hint: Addition."},
                {"q": "Sub-Question 2: 47 birds on a tree. 20 fly away. Left?", "h": "Hint: Subtraction."},
                {"q": "Sub-Question 3: If a problem says 'How many more are needed?', which operation do you use?", "h": "Hint: You are finding the gap."}
            ]
        },
        {
            "topic": "Measuring and Comparing",
            "mastery_q": "A desk is 45 inches long. A bookshelf is 2 feet long. How many inches longer is the desk? (1ft = 12in)",
            "mastery_hint": "Final Hint: 2 feet = 24 inches. Now subtract 24 from 45.",
            "subs": [
                {"q": "Sub-Question 1: Which tool is best for a school bus: Ruler or Measuring Tape?", "h": "Hint: A bus is very long."},
                {"q": "Sub-Question 2: Line A is 15in. Line B is 9in. Difference?", "h": "Hint: 15 minus 9."},
                {"q": "Sub-Question 3: Two 10cm pencils end-to-end. Total?", "h": "Hint: 10 + 10."}
            ]
        },
        {
            "topic": "Time and Money",
            "mastery_q": "An eraser costs 55¢. You have 2 quarters and 2 nickels. Enough money?",
            "mastery_hint": "Final Hint: 25+25+5+5 = 60¢. Compare to 55¢.",
            "subs": [
                {"q": "Sub-Question 1: How many cents is one quarter?", "h": "Hint: 25¢."},
                {"q": "Sub-Question 2: Total for 2 quarters and 1 dime?", "h": "Hint: 25+25+10."},
                {"q": "Sub-Question 3: If the minute hand is at 8, how many minutes is that?", "h": "Hint: Count by fives: 5, 10, 15..."}
            ]
        },
        {
            "topic": "Geometry and Arrays",
            "mastery_q": "Partition a rectangle into 4 rows and 3 columns. Total squares?",
            "mastery_hint": "Final Hint: 3+3+3+3 or 4+4+4.",
            "subs": [
                {"q": "Sub-Question 1: In an array, do rows go across or up-and-down?", "h": "Hint: Movie theater seats."},
                {"q": "Sub-Question 2: 3 rows and 4 columns. Total?", "h": "Hint: Count them all or add."},
                {"q": "Sub-Question 3: Which matches 2 rows and 5 columns? (A) 2+5, (B) 5+5, (C) 2+2+2+2+2, (D) B & C", "h": "Hint: Add the rows or add the columns."}
            ]
        }
    ]
}

# --- SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.grade = "Kindergarten"
    st.session_state.set_idx = 0
    st.session_state.sub_idx = -1 # -1 means we are on Mastery Question
    st.session_state.phase = "familiarity"
    st.session_state.results = []
    st.session_state.mastery_streak = 0
    st.session_state.bottleneck = False

def record(topic, detail, status, hint):
    st.session_state.results.append({
        "Grade": st.session_state.grade,
        "Topic": topic,
        "Detail": detail,
        "Status": status,
        "Hint Used": "Yes" if hint else "No"
    })

# --- UI ---
st.title("Tutor Math Diagnostic")

if st.session_state.step == "setup":
    st.session_state.tutor = st.text_input("Tutor Name")
    st.session_state.student = st.text_input("Student Name")
    st.session_state.curriculum = st.selectbox("Curriculum", ["US Common Core"])
    st.session_state.grade = st.selectbox("Starting Class", ["Kindergarten", "Grade 1", "Grade 2"])
    if st.button("Start"):
        st.session_state.step = "testing"
        st.rerun()

elif st.session_state.step == "testing":
    data = ASSESSMENT_CONTENT[st.session_state.grade][st.session_state.set_idx]
    st.subheader(f"{st.session_state.grade} - {data['topic']}")
    
    if st.session_state.phase == "familiarity":
        st.write(f"**Is the student familiar with {data['topic']}?**")
        c1, c2 = st.columns(2)
        if c1.button("Yes"):
            st.session_state.phase = "mastery"
            st.rerun()
        if c2.button("No"):
            record(data['topic'], "Familiarity", "Not Familiar", False)
            st.session_state.bottleneck = True
            # Move to next set or end
            if st.session_state.set_idx < 4:
                st.session_state.set_idx += 1
            else:
                st.session_state.step = "summary"
            st.rerun()

    elif st.session_state.phase == "mastery":
        st.info(f"**MASTERY QUESTION:** {data['mastery_q']}")
        hint = st.checkbox("Use Hint?")
        if hint: st.warning(data['mastery_hint'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record(data['topic'], "Mastery Q", "Correct", hint)
            st.session_state.mastery_streak += 1
            if st.session_state.set_idx < 4:
                st.session_state.set_idx += 1
                st.session_state.phase = "familiarity"
            else:
                # End of Grade
                if st.session_state.mastery_streak == 5 and not st.session_state.bottleneck:
                    # ADVANCE GRADE
                    grades = list(ASSESSMENT_CONTENT.keys())
                    idx = grades.index(st.session_state.grade)
                    if idx < len(grades)-1:
                        st.session_state.grade = grades[idx+1]
                        st.session_state.set_idx = 0
                        st.session_state.mastery_streak = 0
                        st.session_state.phase = "familiarity"
                        st.success("Mastery Complete! Moving to next Grade.")
                    else: st.session_state.step = "summary"
                else: st.session_state.step = "summary"
            st.rerun()
            
        if c2.button("❌ Incorrect"):
            record(data['topic'], "M
