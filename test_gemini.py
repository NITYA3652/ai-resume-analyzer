"""Run:  python test_gemini.py
Shows which Gemini models work with YOUR key right now."""
import tomllib
from google import genai

key = tomllib.load(open(".streamlit/secrets.toml", "rb"))["GEMINI_API_KEY"]
client = genai.Client(api_key=key)

names = []
for m in client.models.list():
    n = m.name.replace("models/", "")
    if "generateContent" in (getattr(m, "supported_actions", None) or []) and "flash" in n:
        names.append(n)

print(f"Found {len(names)} flash models. Testing each...\n")
for n in names:
    try:
        r = client.models.generate_content(model=n, contents="Reply with the word OK")
        print(f"WORKS   {n}  ->  {r.text.strip()[:20]}")
    except Exception as e:
        print(f"FAILED  {n}  ->  {str(e)[:90]}")
