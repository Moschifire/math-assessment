import streamlit as st

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Math Diagnostic Assessment", layout="centered")

# --- DATA STRUCTURE ---
questions = [
    {
        "id": 1,
        "topic": "Cardinality and Addition",
        "mastery_q": "There are 3 red apples and 2 green apples. How many apples are there in all? Tell me or draw a picture to show how you found the answer.",
        "mastery_hint": "Final Hint: You can count all the apples starting from 1, or start at 3 and count two more.",
        "sub_questions": [
            {"q": "Sub-Question 1: Here is a group of red apples: 🍎 🍎 🍎. Point to each one as you count them. How many are there?", "hint": "Hint: Use your finger to touch each apple as you say the numbers '1, 2...'"},
            {"q": "Sub-Question 2: Here is a group of green apples: 🍏 🍏. How many green apples are there?", "hint": "Hint: Count them just like you did the red ones."},
            {"q": "Sub-Question 3: If we put the red apples and green apples in one big basket, what is the next number you say after '3' to keep counting?", "hint": "Hint: Start at 3 (the red ones) and count on: '3... 4...'"}
        ]
    },
    {
        "id": 2,
        "topic": "Comparing Numbers",
        "mastery_q": "Look at the numbers 7 and 3. Tell me which number is greater than the other and explain how you know.",
        "mastery_hint": "Final Hint: Imagine 7 cookies and 3 cookies. Which plate has more?",
        "sub_questions": [
            {"q": "Sub-Question 1: Group A has 4 stars (⭐) and Group B has 6 stars (⭐). How many are in each group?", "hint": "Hint: Count each group carefully and remember the last number you say."},
            {"q": "Sub-Question 2: If every star in Group A holds hands with a star in Group B, will there be stars left over in Group B?", "hint": "Hint: Draw a line from one star in A to one star in B. See which group has extra."},
            {"q": "Sub-Question 3: Which number is bigger when we count: 4 or 6?", "hint": "Hint: Think about which number comes later when you count to 10."}
        ]
    },
    {
        "id": 3,
        "topic": "Composition & Base Ten",
        "mastery_q": "Look at the number 15. Use blocks or a drawing to show me how this number is made of one group of ten and some extra ones. How many extra ones are there?",
        "mastery_hint": "Final Hint: 15 is the same as 10+___.",
        "sub_questions": [
            {"q": "Sub-Question 1: Use these circles: ⚪. Circle a group of exactly 10. How many are left outside your circle? (Provide 13 circles).", "hint": "Hint: Count out ten circles first and draw a big ring around them."},
            {"q": "Sub-Question 2: If you have 10 circles in a ring and 3 circles outside, how many are there altogether?", "hint": "Hint: Count on from ten: '10... 11, 12, 13.'"},
            {"q": "Sub-Question 3: How do you write the number 'thirteen' using digits?", "hint": "Hint: It has a '1' for the group of ten and a '3' for the extra ones."}
        ]
    },
    {
        "id": 4,
        "topic": "Decomposition",
        "mastery_q": "You have 10 apples total. Some are in a red bag and some are in a blue bag. If 4 apples are in the red bag, how many must be in the blue bag? Show your work.",
        "mastery_hint": "Final Hint: Start with 10 fingers or 10 circles. Take away 4. What is left?",
        "sub_questions": [
            {"q": "Sub-Question 1: I have 5 fingers held up. If I tuck 2 fingers down, how many are still up?", "hint": "Hint: Look at your hand and try it!"},
            {"q": "Sub-Question 2: If we have 10 spots on a tens-frame and 8 are filled, how many are empty?", "hint": "Hint: Count the empty boxes in the frame."},
            {"q": "Sub-Question 3: What number do you need to add to 9 to make 10?", "hint": "Hint: If you have 9, how many more jumps to get to 10?"}
        ]
    },
    {
        "id": 5,
        "topic": "Geometry and Position",
        "mastery_q": "I am a shape. I am solid (3D), I have 6 flat faces that are all squares, and I am sitting beside a cylinder. What shape am I?",
        "mastery_hint": "Final Hint: Think of a toy block or a dice.",
        "sub_questions": [
            {"q": "Sub-Question 1: Look at these shapes. Which one has 3 sides and 3 corners?", "hint": "Hint: It looks like a slice of pie or a mountain."},
            {"q": "Sub-Question 2: Point to the shape that is above the square. (Provide a diagram).", "hint": "Hint: 'Above' means higher up, like the sun is above the trees."},
            {"q": "Sub-Question 3: Is a ball a 'flat' shape (2D) or a 'solid' shape (3D)?", "hint": "Hint: Can you hold it in your hand, or is it just a drawing on paper?"}
        ]
    }
]

# --- SESSION STATE ---
if 'current_set' not in st.session_state:
    st.session_state.current_set = 0
    st.session_state.results = []
    st.session_state.phase = "familiarity" # Stages: familiarity, mastery, subquestions, finished
    st.session_state.sub_idx = 0

# --- HELPER FUNCTIONS ---
def record_result(topic, q_type, status, hint_used):
    st.session_state.results.append({
        "Topic": topic,
        "Question": q_type,
        "Result": status,
        "Hint Used": "Yes" if hint_used else "No"
    })

def next_set():
    st.session_state.current_set += 1
    st.session_state.phase = "familiarity"
    st.session_state.sub_idx = 0
    if st.session_state.current_set >= len(questions):
        st.session_state.phase = "finished"

# --- UI LOGIC ---
st.title("Tutor Assessment Tool: Kindergarten Math")

if st.session_state.phase == "familiarity":
    curr = questions[st.session_state.current_set]
    st.header(f"Set {curr['id']}: {curr['topic']}")
    st.subheader("Is the student familiar with this topic?")
    
    col1, col2 = st.columns(2)
    if col1.button("Yes, proceed"):
        st.session_state.phase = "mastery"
        st.rerun()
    if col2.button("No, skip set"):
        record_result(curr['topic'], "Familiarity", "Not Familiar", False)
        next_set()
        st.rerun()

elif st.session_state.phase == "mastery":
    curr = questions[st.session_state.current_set]
    st.info(f"**MASTERY QUESTION:** {curr['mastery_q']}")
    
    hint_clicked = st.checkbox("Student requested a hint?")
    if hint_clicked:
        st.warning(curr['mastery_hint'])
    
    st.write("---")
    st.write("Tutor Action:")
    c1, c2 = st.columns(2)
    if c1.button("✅ Correct"):
        record_result(curr['topic'], "Mastery Question", "Correct", hint_clicked)
        next_set()
        st.rerun()
    if c2.button("❌ Incorrect"):
        record_result(curr['topic'], "Mastery Question", "Failed", hint_clicked)
        st.session_state.phase = "subquestions"
        st.rerun()

elif st.session_state.phase == "subquestions":
    curr = questions[st.session_state.current_set]
    sub_q = curr['sub_questions'][st.session_state.sub_idx]
    
    st.subheader(f"Diving Deeper: {curr['topic']}")
    st.info(f"**{sub_q['q']}**")
    
    hint_clicked = st.checkbox(f"Show hint for sub-question {st.session_state.sub_idx + 1}")
    if hint_clicked:
        st.warning(sub_q['hint'])
        
    c1, c2 = st.columns(2)
    if c1.button("Next Sub-Question / Correct"):
        record_result(curr['topic'], f"Sub-Question {st.session_state.sub_idx + 1}", "Correct", hint_clicked)
        if st.session_state.sub_idx < 2:
            st.session_state.sub_idx += 1
        else:
            next_set()
        st.rerun()
    if c2.button("Incorrect"):
        record_result(curr['topic'], f"Sub-Question {st.session_state.sub_idx + 1}", "Incorrect", hint_clicked)
        if st.session_state.sub_idx < 2:
            st.session_state.sub_idx += 1
        else:
            next_set()
        st.rerun()

elif st.session_state.phase == "finished":
    st.success("Assessment Complete!")
    st.header("Diagnostic Summary")
    st.table(st.session_state.results)
    
    if st.button("Start New Assessment"):
        st.session_state.current_set = 0
        st.session_state.results = []
        st.session_state.phase = "familiarity"
        st.rerun()
