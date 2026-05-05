import streamlit as st
import pandas as pd
import requests
import json

# --- CONFIG ---
# PASTE YOUR GOOGLE APPS SCRIPT URL HERE
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxFm533cRPJWr3e-XBb0iHWoTJhKi0eERBGxXCJ_rkpMJP1fIyKPh4VmU2xE2F1aTr51g/exec" 

st.set_page_config(page_title="Math Diagnostic Assessment", layout="wide")

# --- DATA: THE FULL CONTENT ---
ASSESSMENT_CONTENT = {
    "Kindergarten": [
        {
            "topic": "Question Set 1: Cardinality and Addition (K.CC.B.4 & K.OA.A.2) - One-to-one counting, cardinality, and representing addition as 'putting together'.",
            "mastery_q": "There are 3 red apples and 2 green apples. How many apples are there in all? Tell me or draw a picture to show how you found the answer.",
            "mastery_hint": "Final Hint: You can count all the apples starting from 1, or start at 3 and count two more.",
            "subs": [
                {"q": "Sub-Question 1: Here is a group of red apples: 🍎 🍎 🍎. Point to each one as you count them. How many are there?", "h": "Hint: Use your finger to touch each apple as you say the numbers '1, 2...'"},
                {"q": "Sub-Question 2: Here is a group of green apples: 🍏 🍏. How many green apples are there?", "h": "Hint: Count them just like you did the red ones."},
                {"q": "Sub-Question 3: If we put the red apples and green apples in one big basket, what is the next number you say after '3' to keep counting?", "h": "Hint: Start at 3 (the red ones) and count on: '3... 4...'"}
            ]
        },
        {
            "topic": "Question Set 2: Comparing Numbers (K.CC.C.6 & K.CC.C.7) - Identifying quantities, matching items 1-to-1 to compare, and using the term 'greater than'.",
            "mastery_q": "Look at the numbers 7 and 3. Tell me which number is greater than the other and explain how you know.",
            "mastery_hint": "Final Hint: Imagine 7 cookies and 3 cookies. Which plate has more?",
            "subs": [
                {"q": "Sub-Question 1: Group A has 4 stars (⭐) and Group B has 6 stars (⭐). How many are in each group?", "h": "Hint: Count each group carefully and remember the last number you say."},
                {"q": "Sub-Question 2: If every star in Group A holds hands with a star in Group B, will there be stars left over in Group B?", "h": "Hint: Draw a line from one star in A to one star in B. See which group has extra."},
                {"q": "Sub-Question 3: Which number is bigger when we count: 4 or 6?", "h": "Hint: Think about which number comes later when you count to 10."}
            ]
        },
        {
            "topic": "Question Set 3: Composition & Base Ten (K.NBT.A.1) - Identifying a group of ten, counting 'extra' ones, and understanding teen numbers as 10+n.",
            "mastery_q": "Look at the number 15. Use blocks or a drawing to show me how this number is made of one group of ten and some extra ones. How many extra ones are there?",
            "mastery_hint": "Final Hint: 15 is the same as 10+___.",
            "subs": [
                {"q": "Sub-Question 1: Use these circles: ⚪. Circle a group of exactly 10. How many are left outside your circle? (Provide 13 circles).", "h": "Hint: Count out ten circles first and draw a big ring around them."},
                {"q": "Sub-Question 2: If you have 10 circles in a ring and 3 circles outside, how many are there altogether?", "h": "Hint: Count on from ten: '10... 11, 12, 13.'"},
                {"q": "Sub-Question 3: How do you write the number 'thirteen' using digits?", "h": "Hint: It has a '1' for the group of ten and a '3' for the extra ones."}
            ]
        },
        {
            "topic": "Question Set 4: Decomposition (K.OA.A.3 & K.OA.A.4) - Identifying parts of a whole, using objects to find missing partners, and number bonds to 10.",
            "mastery_q": "You have 10 apples total. Some are in a red bag and some are in a blue bag. If 4 apples are in the red bag, how many must be in the blue bag? Show your work.",
            "mastery_hint": "Final Hint: Start with 10 fingers or 10 circles. Take away 4. What is left?",
            "subs": [
                {"q": "Sub-Question 1: I have 5 fingers held up. If I tuck 2 fingers down, how many are still up?", "h": "Hint: Look at your hand and try it!"},
                {"q": "Sub-Question 2: If we have 10 spots on a tens-frame and 8 are filled, how many are empty?", "h": "Hint: Count the empty boxes in the frame."},
                {"q": "Sub-Question 3: What number do you need to add to 9 to make 10?", "h": "Hint: If you have 9, how many more jumps to get to 10?"}
            ]
        },
        {
            "topic": "Question Set 5: Geometry and Position (K.G.A.1 & K.G.B.4) - Naming shapes (Circle, Square, Triangle), identifying attributes (sides/corners), and using positional words.",
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
            "topic": "Question Set 1: Addition with Three Numbers (1.OA.A.2 & 1.OA.B.3) - Adding two numbers to make a ten, fluency in adding within 20, and using the associative property.",
            "mastery_q": "Sam has 8 blue blocks, 4 red blocks, and 2 yellow blocks. How many blocks does he have in all?",
            "mastery_hint": "Final Hint: Add the 8 and 2 together first to make a ten, then add the 4.",
            "subs": [
                {"q": "Sub-Question 1: What is 8+2?", "h": "Hint: Use your fingers or a number line to count on from 8."},
                {"q": "Sub-Question 2: What is 10+4?", "h": "Hint: Think about one bundle of ten and four extra ones."},
                {"q": "Sub-Question 3: Which is the easiest way to solve 8+4+2? (Options: A: 8+4 first, B: 4+2 first, C: 8+2 first)", "h": "Hint: Look for two numbers that add up to exactly 10."}
            ]
        },
        {
            "topic": "Question Set 2: Place Value - Tens and Ones (1.NBT.B.2 & 1.NBT.C.4) - Identifying tens and ones digits, and adding multiples of 10.",
            "mastery_q": "What is 43 + 10?",
            "mastery_hint": "Final Hint: Add one more ten to the tens place, but keep the ones place the same.",
            "subs": [
                {"q": "Sub-Question 1: In the number 43, which digit is in the tens place?", "h": "Hint: The tens place is the first digit on the left in a 2-digit number."},
                {"q": "Sub-Question 2: How many ones are in the number 43?", "h": "Hint: The ones place is the digit on the right."},
                {"q": "Sub-Question 3: What is 10 more than 40?", "h": "Hint: Count up by tens: 10, 20, 30, 40... what is next?"}
            ]
        },
        {
            "topic": "Question Set 3: Comparing Two-Digit Numbers (1.NBT.B.3) - Comparing tens digits and understanding the symbols > and <.",
            "mastery_q": "Which math sentence is correct? (Options: A: 42>51, B: 38<35, C: 67>63, D: 21=12)",
            "mastery_hint": "Final Hint: First look at the tens. If the tens are the same, look at the ones to see which is greater.",
            "subs": [
                {"q": "Sub-Question 1: Which number has more tens: 52 or 25?", "h": "Hint: Look at the first digit of each number."},
                {"q": "Sub-Question 2: What does this symbol mean: >?", "h": "Hint: The 'mouth' opens toward the bigger number."},
                {"q": "Sub-Question 3: Which number makes this true: 15 < ___?", "h": "Hint: You need a number that is bigger than 15."}
            ]
        },
        {
            "topic": "Question Set 4: Telling Time (1.MD.B.3) - Identifying hour/minute hands and 'o'clock' vs 'half past'.",
            "mastery_q": "The short hand is between the 7 and the 8. The long hand is on the 6. What time is it?",
            "mastery_hint": "Final Hint: It is halfway past the 7. Write the time using a colon (:).",
            "subs": [
                {"q": "Sub-Question 1: On a clock, which hand is shorter: the hour hand or the minute hand?", "h": "Hint: The shorter hand tells us what hour it is."},
                {"q": "Sub-Question 2: When the long minute hand points to the 12, it is:", "h": "Hint: This is the start of a brand new hour."},
                {"q": "Sub-Question 3: When the long minute hand points to the 6, it is:", "h": "Hint: The hand has moved halfway around the circle."}
            ]
        },
        {
            "topic": "Question Set 5: Geometry - Partitioning Circles and Rectangles (1.G.A.3) - Defining 'equal shares' and identifying halves/fourths.",
            "mastery_q": "If you take a square and fold it in half, and then fold it in half again, what are the 4 new equal shapes called?",
            "mastery_hint": "Final Hint: 'Fourths' and 'Quarters' mean the shape is split into 4 equal pieces.",
            "subs": [
                {"q": "Sub-Question 1: If I cut a cake into 2 parts, but one part is much bigger than the other, are they 'equal shares'?", "h": "Hint: Equal shares must be the exact same size."},
                {"q": "Sub-Question 2: If you divide a circle into two equal shares, what is one of those shares called?", "h": "Hint: Think of sharing a cookie between two people."},
                {"q": "Sub-Question 3: How many equal shares are in a 'quarter' of a shape?", "h": "Hint: It is the same as the number of wheels on a car."}
            ]
        }
    ],
    "Grade 2": [
        {
            "topic": "Question Set 1: Place Value to 1,000 (2.NBT.A.1 & 2.NBT.A.3) - Identifying digits in HTO places, value of digits, and expanded form.",
            "mastery_q": "I am a number. I have 5 hundreds, 16 tens, and 2 ones. What number am I in standard form?",
            "mastery_hint": "Final Hint: First, find the value of 5 hundreds (500). Then find the value of 16 tens (160). Add 500 + 160 + 2.",
            "subs": [
                {"q": "Sub-Question 1: In the number 706, which digit is in the tens place?", "h": "Hint: Look at the middle digit. If there are 'no tens', what number represents that?"},
                {"q": "Sub-Question 2: What is the value of the digit 8 in the number 853?", "h": "Hint: The 8 is in the hundreds place. Think about 8 bundles of 100."},
                {"q": "Sub-Question 3: Write the number 432 in expanded form (using + signs).", "h": "Hint: Break it into hundreds + tens + ones (400+___+___)."}
            ]
        },
        {
            "topic": "Question Set 2: Multi-Step Addition & Subtraction (2.OA.A.1) - Adding within 100 and solving two-step word problems.",
            "mastery_q": "A baker made 80 muffins. He sold 25 in the morning and 30 in the afternoon. How many muffins does he have left?",
            "mastery_hint": "Final Hint: This is a two-step problem. First, add the muffins sold (25+30). Then, subtract that total from 80.",
            "subs": [
                {"q": "Sub-Question 1: There were 35 birds on a tree. 12 more birds flew to the tree. How many are there now?", "h": "Hint: Use addition to find the new total."},
                {"q": "Sub-Question 2: There are 47 birds on a tree. 20 birds fly away. How many birds are left?", "h": "Hint: Use subtraction to find the difference."},
                {"q": "Sub-Question 3: If a problem says 'How many more are needed?' which operation should you usually use to find the answer?", "h": "Hint: You are finding the gap between a small number and a target number."}
            ]
        },
        {
            "topic": "Question Set 3: Measuring and Comparing Lengths (2.MD.A.1 & 2.MD.A.4) - Choosing tools, measuring units, and calculating length difference.",
            "mastery_q": "A desk is 45 inches long. A bookshelf is 2 feet long. How many inches longer is the desk? (Note: 1 foot = 12 inches).",
            "mastery_hint": "Final Hint: First, turn the 2 feet into inches (12+12=24). Then, subtract 24 from 45.",
            "subs": [
                {"q": "Sub-Question 1: Which tool is best for measuring the length of a real school bus?", "h": "Hint: A bus is very long; you need a tool that can reach many feet."},
                {"q": "Sub-Question 2: Line A is 15 inches long. Line B is 9 inches long. How much longer is Line A than Line B?", "h": "Hint: Subtract the length of the shorter line from the longer line (15−9)."},
                {"q": "Sub-Question 3: If you place two 10cm pencils end-to-end, what is their total length?", "h": "Hint: Add 10+10."}
            ]
        },
        {
            "topic": "Question Set 4: Time and Money (2.MD.C.7 & 2.MD.C.8) - Coin values, adding money, and telling time to 5 minutes.",
            "mastery_q": "An eraser costs 55¢. You have 2 quarters and 2 nickels. Do you have enough money? (Answer 'Yes' or 'No').",
            "mastery_hint": "Final Hint: First, find your total money (25+25+5+5). Then compare that number to 55¢.",
            "subs": [
                {"q": "Sub-Question 1: How many cents is one quarter worth?", "h": "Hint: It is the largest common silver coin; four of them make a dollar."},
                {"q": "Sub-Question 2: You have 2 quarters and 1 dime. How many cents do you have in total?", "h": "Hint: 25+25+10=___"},
                {"q": "Sub-Question 3: If the minute hand is pointing at the 8, how many minutes past the hour is it?", "h": "Hint: Count by fives around the clock."}
            ]
        },
        {
            "topic": "Question Set 5: Geometry and Arrays (2.G.A.2 & 2.OA.C.4) - Rows/Columns, total count in arrays, and repeated addition.",
            "mastery_q": "Partition a rectangle into 4 rows and 3 columns of same-size squares. How many squares are there in total? Write the repeated addition sentence used to find the answer.",
            "mastery_hint": "Final Hint: 3+3+3+3 (adding the columns) or 4+4+4 (adding the rows).",
            "subs": [
                {"q": "Sub-Question 1: In an array, do rows go across (left-to-right) or up-and-down?", "h": "Hint: Think about the rows of seats in a movie theater."},
                {"q": "Sub-Question 2: A chocolate bar has 3 rows and 4 columns of squares. How many total squares are there?", "h": "Hint: You can count them all, or add 4+4+4."},
                {"q": "Sub-Question 3: Which addition sentence matches an array with 2 rows and 5 columns? (Options: A: 2+5, B: 5+5, C: 2+2+2+2+2, D: Both B and C)", "h": "Hint: You can add the number in each row (5+5) or the number in each column (2+2+2+2+2)."}
            ]
        }
    ]
}

# --- PERMANENT SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "setup"
    st.session_state.p_grade = "Kindergarten"
    st.session_state.p_tutor = ""
    st.session_state.p_student = ""
    st.session_state.p_curr = "US Common Core"
    st.session_state.set_idx = 0
    st.session_state.sub_idx = 0
    st.session_state.phase = "familiarity"
    st.session_state.results = []
    st.session_state.mastery_streak = 0
    st.session_state.bottleneck = False

def record_entry(topic, detail, status, hint):
    st.session_state.results.append({
        "Grade": st.session_state.p_grade,
        "Topic": topic,
        "Level": detail,
        "Status": status,
        "Hint Used": "Yes" if hint else "No"
    })

# --- UI LOGIC ---
if st.session_state.step == "setup":
    st.title("Diagnostic Assessment Tool")
    t_tutor = st.text_input("Tutor Name")
    t_student = st.text_input("Student Name")
    t_curr = st.selectbox("Curriculum", ["US Common Core", "UK National", "IB"])
    t_grade = st.selectbox("Starting Class", ["Kindergarten", "Grade 1", "Grade 2"])
    
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

elif st.session_state.step == "testing":
    cur_grade = st.session_state.p_grade
    data = ASSESSMENT_CONTENT[cur_grade][st.session_state.set_idx]
    
    st.title(f"{cur_grade} Assessment")
    st.info(f"Student: {st.session_state.p_student} | Tutor: {st.session_state.p_tutor}")

    if st.session_state.phase == "familiarity":
        st.subheader(data['topic'])
        st.write("Is the student familiar with this topic?")
        c1, c2 = st.columns(2)
        if c1.button("Yes, proceed"):
            st.session_state.phase = "mastery"
            st.rerun()
        if c2.button("No, skip to next topic"):
            record_entry(data['topic'], "Familiarity Check", "Not Familiar", False)
            st.session_state.bottleneck = True
            if st.session_state.set_idx < 4:
                st.session_state.set_idx += 1
                st.session_state.phase = "familiarity"
            else:
                st.session_state.step = "summary"
            st.rerun()

    elif st.session_state.phase == "mastery":
        st.subheader("Mastery Level")
        st.write(data['mastery_q'])
        h_used = st.checkbox("Show Hint to student?")
        if h_used: st.warning(data['mastery_hint'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct"):
            record_entry(data['topic'], "Mastery Q", "Correct", h_used)
            st.session_state.mastery_streak += 1
            if st.session_state.set_idx < 4:
                st.session_state.set_idx += 1
                st.session_state.phase = "familiarity"
            else:
                # Grade Advance Logic
                if st.session_state.mastery_streak == 5 and not st.session_state.bottleneck:
                    grades = list(ASSESSMENT_CONTENT.keys())
                    idx = grades.index(cur_grade)
                    if idx < len(grades)-1:
                        st.session_state.p_grade = grades[idx+1]
                        st.session_state.set_idx = 0
                        st.session_state.mastery_streak = 0
                        st.session_state.phase = "familiarity"
                        st.success(f"Advancing to {st.session_state.p_grade}...")
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
        st.subheader(f"Sub-Question {st.session_state.sub_idx + 1}")
        sub = data['subs'][st.session_state.sub_idx]
        st.write(sub['q'])
        h_used = st.checkbox(f"Show hint?")
        if h_used: st.warning(sub['h'])
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Correct / Next"):
            record_entry(data['topic'], f"Sub-Q {st.session_state.sub_idx + 1}", "Correct", h_used)
            if st.session_state.sub_idx < 2:
                st.session_state.sub_idx += 1
            else:
                if st.session_state.set_idx < 4:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()
        if c2.button("❌ Incorrect"):
            record_entry(data['topic'], f"Sub-Q {st.session_state.sub_idx + 1}", "Incorrect", h_used)
            if st.session_state.sub_idx < 2:
                st.session_state.sub_idx += 1
            else:
                if st.session_state.set_idx < 4:
                    st.session_state.set_idx += 1
                    st.session_state.phase = "familiarity"
                else: st.session_state.step = "summary"
            st.rerun()

elif st.session_state.step == "summary":
    st.header("Assessment Summary")
    df = pd.DataFrame(st.session_state.results)
    st.table(df)
    
    # Format detailed text for Google Sheet
    report_body = ""
    for r in st.session_state.results:
        report_body += f"[{r['Grade']}] {r['Topic']} | {r['Level']}: {r['Status']} (Hint: {r['Hint Used']})\n"

    if st.button("Submit to Google Sheets"):
        payload = {
            "tutor": st.session_state.p_tutor,
            "student": st.session_state.p_student,
            "curriculum": st.session_state.p_curr,
            "grade": st.session_state.p_grade,
            "results": report_body
        }
        try:
            r = requests.post(WEBHOOK_URL, data=json.dumps(payload))
            if r.status_code == 200: st.success("Assessment submitted successfully.")
            else: st.error("Server Error.")
        except:
            st.error("Submission failed.")
