# 📄 AI Resume Analyzer

An AI-powered tool that lets users upload their resume and receive an **ATS compatibility
score**, along with **missing skills**, **grammar issues**, and **personalised suggestions**
for improvement - helping job seekers optimise their resumes before applying.

## Features
- Upload resume as PDF, DOCX or TXT
- Transparent rule-based ATS score out of 100 (contact info, sections, length, action verbs, metrics, bullets)
- AI-powered (Google Gemini) skill-gap analysis, optionally against a pasted job description
- Grammar and wording fixes
- Prioritised improvement suggestions and rewritten bullet points

## Tech Stack
Python, Streamlit, Google Gemini API (`google-genai`), pypdf, python-docx

## Run locally
```bash
git clone https://github.com/<your-username>/ai-resume-analyzer.git
cd ai-resume-analyzer
python -m venv venv
venv\Scripts\activate        # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```
Create `.streamlit/secrets.toml` (copy from `secrets.toml.example`) and add your Gemini API key, then:
```bash
streamlit run app.py
```

## Project structure
| File | Purpose |
|---|---|
| `app.py` | Streamlit user interface |
| `resume_parser.py` | Extracts text from PDF/DOCX/TXT |
| `ats_checks.py` | Rule-based ATS scoring |
| `ai_analyzer.py` | Gemini API call + JSON parsing |

## Live demo
https://ai-resume-analyzer-mksfpyc6xajdi9za6bjgks.streamlit.app/
