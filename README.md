# Multi-Subject Diagnostic Pro

A professional, AI-powered educational diagnostic tool built with **Streamlit**, **Supabase**, and **Google Gemini**. This application allows tutors to conduct scaffolded Mathematics assessments and linear English Language assessments, automatically generates personalized 12-week learning plans, and provides a secure admin dashboard with PDF export capabilities.

## 🚀 Key Features

### 1. Dual-Engine Diagnostic Logic
*   **Mathematics (Scaffolded):** Uses a "Mastery ➡️ Sub-questions ➡️ Mastery Retry" flow. If a student fails a high-level concept, the app breaks it down into foundational sub-skills before allowing a retry.
*   **English Language (Linear):** Designed for reading comprehension and phonics. It presents sections of material (text/images) and iterates through all questions in a section to check for consistent understanding.

### 2. Intelligent Grade Transitions & Bottlenecks
*   **Auto-Leveling:** If a student achieves 100% mastery in their starting grade, the app automatically transitions them to the next grade level.
*   **The Bottleneck:** To protect student confidence, the assessment ends immediately if a student hits a knowledge gap (Incorrect or "Not Familiar" answer) in any grade level higher than their starting point.

### 3. AI-Powered Personalized Reporting
*   Integrates with **Google Gemini (2.5 Flash & Pro)** via a high-availability fallback chain.
*   Generates a **General Performance Overview** and a **Theme-by-Theme Analysis**.
*   Produces a **12-Week Personalized Learning Plan** formatted as a structured Markdown table.

### 4. Secure Admin Dashboard
*   **Password Protected:** Access to student data is restricted by a secret admin key.
*   **Record Management:** View every assessment attempt uniquely identified by student name, subject, and timestamp.
*   **PDF Export:** Generate professional **Landscape 2-Column PDF Reports** containing the assessment log, tutor feedback, and the AI learning table.

### 5. Universal Image Loader
*   Seamlessly renders images from **Google Drive** and **Craft.do**.
*   Supports **Image Grids** for multiple-choice questions in the English engine.

---

## 🛠️ Tech Stack
*   **Frontend:** Streamlit
*   **Language:** Python 3.x
*   **Database:** Supabase (PostgreSQL)
*   **AI Agent:** Google Gemini API
*   **PDF Engine:** FPDF2
*   **Data Store:** JSON (GitHub-hosted Question Bank)

---

## 📂 Project Structure
```text
├── app.py              # The main application logic engine
├── content.json        # The dynamic question bank (edit this to add/change questions)
├── requirements.txt    # Python dependencies
└── .streamlit/
    └── secrets.toml    # API keys and Database credentials (local only)
```

---

## ⚙️ Setup & Deployment

### 1. Database Setup (Supabase)
Create a table in your Supabase SQL Editor:
```sql
create table assessment_results (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default now(),
  tutor text,
  student text,
  subject text,
  curriculum text,
  grade text,
  results text,
  feedback text,
  ai_plan text
);
```

### 2. Secrets Configuration
In Streamlit Cloud (or `secrets.toml` locally), add the following:
```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-anon-public-key"
GEMINI_API_KEY = "your-google-ai-studio-key"
ADMIN_PASSWORD = "your-admin-dashboard-password"
```

### 3. Question Bank (`content.json`)
The app builds itself based on this file. Structure:
*   **Level 1:** Subject (Mathematics / English Language)
*   **Level 2:** Curriculum (e.g., US Common Core)
*   **Level 3:** Grade (e.g., Year 1)
*   **Level 4:** Question Sets

---

## 📝 Usage for Tutors

1.  **Setup:** Enter the Student and Tutor names and select the subject/grade.
2.  **Familiarity:** Ask the student if they know the topic before showing questions.
3.  **Assessment:** 
    *   For **Math**, click Correct/Incorrect. The app handles the branching logic automatically.
    *   For **English**, have the student read the material and answer all questions in the section.
4.  **Summary:** Review the results log. Click **"Generate AI Learning Plan"** to create the 12-week roadmap.
5.  **Save:** Click **"Save to Database"** to send the report to the Admin Dashboard.

## 📝 Usage for Admins

1.  Navigate to **Admin Dashboard** in the sidebar.
2.  Enter the **Admin Password**.
3.  View the table of recent assessments.
4.  Select a specific assessment from the dropdown.
5.  Click **"Download PDF"** to generate the parent-facing report.

---

## ⚠️ Maintenance Notes
*   **Updating Questions:** Always validate your `content.json` using a JSON Linter before pushing to GitHub to avoid syntax crashes.
*   **API Limits:** Ensure your Google AI Studio account is active for the Gemini API.
*   **Images:** Ensure Google Drive images are set to "Anyone with the link can view."
