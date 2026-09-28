"""
Rule-based ATS checks (no AI needed).
These run locally and give a transparent, explainable score out of 100.
"""
import re

SECTION_KEYWORDS = {
    "Contact info": [],  # checked separately with regex
    "Summary / Objective": ["summary", "objective", "profile", "about me"],
    "Education": ["education", "academic", "qualification"],
    "Experience": ["experience", "employment", "internship", "work history"],
    "Skills": ["skills", "technologies", "technical skills", "competencies"],
    "Projects": ["projects", "project work"],
}

ACTION_VERBS = {
    "developed", "built", "designed", "implemented", "created", "led", "managed",
    "improved", "optimized", "analyzed", "automated", "deployed", "launched",
    "reduced", "increased", "achieved", "collaborated", "engineered", "delivered",
    "architected", "integrated", "streamlined", "coordinated", "trained", "tested",
}

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{8,}\d)")
LINK_RE = re.compile(r"(linkedin\.com|github\.com)", re.I)
NUMBER_RE = re.compile(r"\b\d+(\.\d+)?\s?(%|x|\+|k|K|lpa|users|projects)?")


def run_ats_checks(text: str) -> dict:
    """Return {'score': int, 'checks': [ {name, passed, points, max, tip} ]}."""
    lower = text.lower()
    words = re.findall(r"[A-Za-z']+", text)
    word_count = len(words)
    checks = []

    def add(name, passed, max_pts, tip, partial=None):
        pts = max_pts if passed else (partial if partial is not None else 0)
        checks.append({"name": name, "passed": passed, "points": pts,
                       "max": max_pts, "tip": tip})

    # 1. Contact information 
    add("Email address", bool(EMAIL_RE.search(text)), 7,
        "Add a professional email address at the top of your resume.")
    add("Phone number", bool(PHONE_RE.search(text)), 7,
        "Add a phone number so recruiters can reach you.")
    add("LinkedIn / GitHub link", bool(LINK_RE.search(text)), 6,
        "Add your LinkedIn or GitHub profile link.")

    # 2. Standard sections
    for section, keys in SECTION_KEYWORDS.items():
        if section == "Contact info":
            continue
        found = any(re.search(rf"\b{re.escape(k)}\b", lower) for k in keys)
        add(f"'{section}' section", found, 5,
            f"Add a clearly labelled '{section}' heading - ATS software looks for it.")

    # 3. Length
    if 300 <= word_count <= 900:
        add("Resume length", True, 15, "")
    elif 150 <= word_count < 300 or 900 < word_count <= 1200:
        add("Resume length", False, 15,
            f"Your resume has {word_count} words. Aim for 300-900 (about 1 page for freshers).",
            partial=8)
    else:
        add("Resume length", False, 15,
            f"Your resume has {word_count} words - that is far outside the ideal 300-900 range.")

    # 4. Action verbs
    verbs_found = {w.lower() for w in words} & ACTION_VERBS
    if len(verbs_found) >= 6:
        add("Strong action verbs", True, 15, "")
    else:
        add("Strong action verbs", False, 15,
            "Start bullet points with verbs like 'Developed', 'Built', 'Optimized'. "
            f"You used {len(verbs_found)} - aim for 6+.",
            partial=min(14, len(verbs_found) * 2))

    # 5. Quantified achievements
    numbers = [m for m in NUMBER_RE.finditer(text)]
    if len(numbers) >= 5:
        add("Numbers / measurable results", True, 10, "")
    else:
        add("Numbers / measurable results", False, 10,
            "Add measurable results, e.g. 'Improved accuracy by 12%' or 'Built app used by 200 students'.",
            partial=min(9, len(numbers) * 2))

    # 6. Bullet points 
    bullets = len(re.findall(r"^\s*[-•●▪*·]", text, flags=re.M))
    add("Bullet-point formatting", bullets >= 5, 10,
        "Use bullet points to describe experience/projects - they are easier for ATS and humans to scan.",
        partial=5 if bullets >= 2 else 0)

    score = sum(c["points"] for c in checks)
    total = sum(c["max"] for c in checks)
    return {"score": round(score / total * 100), "checks": checks,
            "word_count": word_count}
