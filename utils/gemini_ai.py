"""
Gemini AI insights — returns structured ATS coaching feedback.
Requires GEMINI_API_KEY in .env
"""
import os
from google import genai # Change: Import directly from google
from dotenv import load_dotenv

load_dotenv()

# We store the client here once initialized
_client = None

def _init():
    global _client
    if _client:
        return _client
    
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_gemini_api_key_here":
        print("      GEMINI_API_KEY not set — AI insights will be skipped")
        return None
    
    # NEW: Create a Client instead of using genai.configure()
    _client = genai.Client(api_key=key)
    return _client


def get_ai_insights(resume_text: str, job_desc: str) -> str:
    client = _init()
    if not client:
        return (
            "AI insights unavailable.\n"
            "Add your Gemini API key to the .env file:\n"
            "  GEMINI_API_KEY=your_key_here"
        )
    try:
        # NEW: Use client.models.generate_content
        # Using gemini-3-flash for significantly faster results
        prompt = f"""You are a senior ATS specialist and career coach.

Analyse the resume against the job description and respond using EXACTLY this format:

**STRENGTHS**
- [strength 1]
- [strength 2]
- [strength 3]

**GAPS**
- [gap 1]
- [gap 2]
- [gap 3]

**QUICK WINS**
- [actionable fix 1]
- [actionable fix 2]
- [actionable fix 3]

**VERDICT**
[One concise sentence on overall fit and hire-ability]

**EXPETIENCE IMPROVEMENT**
[One concise sentence on how the candidate can improve their experience to be a better fit for the

**RESUME FORMAT**
[One concise sentence on the format and structure of the resume]

**SUGGESTED JOB TITLE**
[One relevant job title that matches the resume and job description]
---
RESUME:
{resume_text[:4500]}

JOB DESCRIPTION:
{job_desc[:2000]}
"""
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return resp.text if resp else "No response from Gemini."
        
    except Exception as e:
        return f"Gemini error: {e}"