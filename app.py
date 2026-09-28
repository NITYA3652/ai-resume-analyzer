"""AI Resume Analyzer - Streamlit web app."""
import os

import streamlit as st

from ai_analyzer import analyze_resume
from ats_checks import run_ats_checks
from resume_parser import extract_text

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")


def get_api_key() -> str:
    """Look for the key in Streamlit secrets, then env variable."""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY", "")


def score_color(score: int) -> str:
    return "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"


# ---------- Header ----------
st.title("📄 AI Resume Analyzer")
st.caption("Upload your resume and get an ATS compatibility score, missing skills, "
           "grammar fixes, and personalised suggestions - before you apply.")

api_key = get_api_key()
with st.sidebar:
    st.header("⚙️ Settings")
    if not api_key:
        api_key = st.text_input("Gemini API key", type="password",
                                help="Get a free key at aistudio.google.com")
    else:
        st.success("API key loaded ✔")
    st.markdown("---")
    st.markdown("**How it works**\n\n1. Upload resume (PDF/DOCX/TXT)\n"
                "2. (Optional) paste a job description\n3. Click **Analyze**")

# ---------- Inputs ----------
col_a, col_b = st.columns(2)
with col_a:
    uploaded = st.file_uploader("Upload your resume", type=["pdf", "docx", "txt"])
with col_b:
    job_desc = st.text_area("Target job description (optional, gives better skill-gap results)",
                            height=150, placeholder="Paste the job posting here...")

if st.button("🔍 Analyze Resume", type="primary", use_container_width=True):
    if not uploaded:
        st.warning("Please upload a resume first.")
        st.stop()
    if not api_key:
        st.warning("Please provide a Gemini API key in the sidebar.")
        st.stop()

    try:
        text = extract_text(uploaded)
    except Exception as e:
        st.error(f"Could not read the file: {e}")
        st.stop()

    if len(text) < 100:
        st.error("Very little text was found. If your resume is a scanned image, "
                 "please upload a text-based PDF or DOCX instead.")
        st.stop()

    ats = run_ats_checks(text)

    with st.spinner("AI is reviewing your resume..."):
        try:
            ai = analyze_resume(api_key, text, job_desc)
        except Exception as e:
            st.error(f"AI analysis failed: {e}")
            st.stop()

    st.divider()

    # ---------- Score ----------
    c1, c2, c3 = st.columns(3)
    c1.metric("ATS Compatibility Score", f"{score_color(ats['score'])} {ats['score']}/100")
    c2.metric("Word Count", ats["word_count"])
    c3.metric("Target Role (detected)", ai.get("detected_role", "N/A"))
    st.progress(ats["score"] / 100)
    st.info(ai.get("summary", ""))

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["✅ ATS Checks", "🧩 Skills", "✍️ Grammar", "💡 Suggestions", "🔧 Better Bullets"])

    with tab1:
        for c in ats["checks"]:
            icon = "✅" if c["passed"] else "❌"
            st.markdown(f"{icon} **{c['name']}** - {c['points']}/{c['max']} pts")
            if not c["passed"] and c["tip"]:
                st.caption(f"↳ {c['tip']}")

    with tab2:
        left, right = st.columns(2)
        with left:
            st.subheader("Skills found")
            found = ai.get("skills_found", [])
            st.write(" ".join(f"`{s}`" for s in found) if found else "None detected.")
        with right:
            st.subheader("Missing skills")
            for m in ai.get("missing_skills", []):
                st.markdown(f"- **{m.get('skill', '')}** - {m.get('why', '')}")

    with tab3:
        issues = ai.get("grammar_issues", [])
        if not issues:
            st.success("No grammar issues found. Nice work!")
        for g in issues:
            st.markdown(f"**{g.get('issue', 'Issue')}**")
            st.markdown(f"❌ ~~{g.get('original', '')}~~")
            st.markdown(f"✅ {g.get('fix', '')}")
            st.markdown("---")

    with tab4:
        order = {"High": 0, "Medium": 1, "Low": 2}
        sugg = sorted(ai.get("suggestions", []), key=lambda s: order.get(s.get("priority"), 3))
        for s in sugg:
            badge = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}.get(s.get("priority"), "⚪")
            st.markdown(f"{badge} **{s.get('section', '')}** ({s.get('priority', '')}): "
                        f"{s.get('suggestion', '')}")

    with tab5:
        for b in ai.get("improved_bullets", []):
            st.markdown(f"**Before:** {b.get('before', '')}")
            st.markdown(f"**After:** {b.get('after', '')}")
            st.markdown("---")

    st.caption(f"Model used: {ai.get('_model_used')}")
