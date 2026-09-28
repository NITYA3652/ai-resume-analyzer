"""Talks to the Gemini API and returns structured feedback about a resume."""
import json
import re
import time

from google import genai
from google.genai import types

# We try the newest model first, then fall back to older ones.
# (Google retires models over time, so having fallbacks keeps the app working.)
MODEL_CANDIDATES = [
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
]

RETRIES_PER_MODEL = 2      # how many times to retry one model
WAIT_SECONDS = [2, 4]  # wait between retries (helps with 503 "high demand")

PROMPT_TEMPLATE = """You are an expert resume reviewer and ATS (Applicant Tracking System) specialist.

Analyze the RESUME below{jd_clause}. Respond ONLY with a JSON object (no markdown fences) with exactly these keys:

{{
  "summary": "2-3 sentence overall assessment of the resume",
  "detected_role": "the job role this resume seems to target",
  "skills_found": ["skills clearly present in the resume"],
  "missing_skills": [
    {{"skill": "skill name", "why": "one short reason it matters for the target role"}}
  ],
  "grammar_issues": [
    {{"original": "exact text with the problem", "fix": "corrected text", "issue": "type of problem"}}
  ],
  "suggestions": [
    {{"section": "which section", "suggestion": "specific, actionable improvement", "priority": "High|Medium|Low"}}
  ],
  "improved_bullets": [
    {{"before": "a weak bullet from the resume", "after": "a stronger rewritten version"}}
  ]
}}

Rules:
- Give 5-10 missing_skills, up to 8 grammar_issues, 5-8 suggestions, and 3 improved_bullets.
- If there are no grammar issues, return an empty list.
- Be specific and honest. Never invent experience the candidate does not have.
- Keep every string concise.

{jd_block}RESUME:
\"\"\"
{resume}
\"\"\"
"""


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.S)
        if match:
            return json.loads(match.group(0))
        raise


def _discover_models(client) -> list:
    """Ask the API which text models this key can actually use."""
    skip = ["image", "tts", "live", "audio", "embedding", "native", "robotics",
            "computer", "vision", "imagen", "veo", "gemma", "learnlm", "aqa"]
    found = []
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            actions = getattr(m, "supported_actions", None) or []
            if ("generateContent" in actions and "gemini" in name
                    and "flash" in name and not any(x in name for x in skip)):
                found.append(name)
    except Exception:
        pass
    return found


def analyze_resume(api_key: str, resume_text: str, job_description: str = "") -> dict:
    client = genai.Client(api_key=api_key)

    if job_description.strip():
        jd_clause = " against the JOB DESCRIPTION provided"
        jd_block = f'JOB DESCRIPTION:\n"""\n{job_description.strip()[:6000]}\n"""\n\n'
    else:
        jd_clause = " (no job description was given, so infer the most likely target role)"
        jd_block = ""

    prompt = PROMPT_TEMPLATE.format(
        jd_clause=jd_clause, jd_block=jd_block, resume=resume_text[:12000]
    )

    # Our preferred models first, then anything else Flash-like the key can use
    models = list(MODEL_CANDIDATES)
    for m in _discover_models(client):
        if m not in models:
            models.append(m)

    last_error = None
    for model in models:
        for attempt in range(RETRIES_PER_MODEL):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.3,
                    ),
                )
                data = _parse_json(response.text)
                data["_model_used"] = model
                return data
            except Exception as e:
                last_error = e
                msg = str(e)
                # Bad key / bad request: retrying will not help, stop immediately
                if "API key" in msg or "PERMISSION_DENIED" in msg or "INVALID_ARGUMENT" in msg:
                    raise RuntimeError(f"API key problem: {msg}")
                # Model does not exist (retired): skip to the next model
                if "NOT_FOUND" in msg or "404" in msg:
                    break
                # 503 overloaded / 429 rate limit / JSON glitch: wait and retry
                time.sleep(WAIT_SECONDS[min(attempt, len(WAIT_SECONDS) - 1)])

    raise RuntimeError(
        "Google's Gemini servers are busy right now. Please wait a minute and click "
        f"Analyze again. (Last error: {last_error})"
    )
