import json
from llm import ask_json

SYSTEM = """You are a strict recruiter-side screener. Compare the candidate profile with the job description.
Return ONLY JSON: {"score": 0-100, "matched_skills": [], "missing_skills": [], "required_certifications": [],
"seniority_fit": "good|too_senior|too_junior", "reason": "one sentence"}.
Score honestly: penalise missing must-have requirements, wrong seniority, and non-sales roles."""

def score_job(job, profile, cfg):
    user = f"TARGET ROLES: {cfg['search']['roles']}\nPROFILE:\n{json.dumps(profile)}\n\nJOB: {job.title} at {job.company} ({job.location})\n{job.description[:6000]}"
    res = None
    try:
        res = ask_json(cfg, SYSTEM, user, 800)
    except Exception as e:
        print("   ! LLM scoring failed, using keyword fallback:", type(e).__name__)
    if res and "score" in res:
        return res
    # Offline fallback: keyword overlap
    text = (job.title + " " + job.description).lower()
    skills = profile.get("skills", [])
    hit = [s for s in skills if s.lower() in text]
    ratio = len(hit) / max(1, min(len(skills), 8))
    return {"score": int(min(100, 40 + 60 * ratio)), "matched_skills": hit, "missing_skills": [],
            "required_certifications": [], "seniority_fit": "unknown", "reason": "keyword fallback (no API key)"}
