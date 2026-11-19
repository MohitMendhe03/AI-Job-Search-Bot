import json, os, re
from llm import ask_json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

SYSTEM = """You tailor a resume for one specific job using ONLY facts in the candidate profile.
Rules: never invent skills, tools, employers, numbers, certifications or dates. You may reorder, select, and reword
for relevance, and mirror keywords from the job description ONLY where the candidate truly has that skill.
Return ONLY JSON:
{"summary": "2-3 sentences", "skills": ["ordered, most relevant first, from profile skills"],
 "experience": [{"company": "exact name from profile", "bullets": ["most relevant first, max 5"]}],
 "certifications": ["only from profile"], "cover_letter": "120-170 words, plain text, specific to the company"}"""

def _nums(s):
    return set(re.findall(r"\d+(?:\.\d+)?", s))

def tailor(job, profile, match, cfg):
    user = f"PROFILE:\n{json.dumps(profile)}\n\nJOB: {job.title} at {job.company}, {job.location}\n{job.description[:6000]}\n\nMATCH NOTES: {json.dumps(match)}"
    out = None
    try:
        out = ask_json(cfg, SYSTEM, user, 3000)
    except Exception as e:
        print("   ! LLM tailoring failed, using master resume:", type(e).__name__)
    return _validate(out, job, profile)

def _validate(out, job, profile):
    """Enforce truthfulness in code, regardless of what the model returned."""
    out = out or {}
    pskills = {s.lower(): s for s in profile.get("skills", [])}
    skills = [pskills[s.lower()] for s in out.get("skills", []) if s.lower() in pskills]
    skills += [s for s in profile.get("skills", []) if s not in skills]
    pcerts = {c.lower(): c for c in profile.get("certifications", [])}
    certs = [pcerts[c.lower()] for c in out.get("certifications", []) if c.lower() in pcerts] or profile.get("certifications", [])
    allowed_nums = _nums(json.dumps(profile))
    exp = []
    chosen = {e.get("company"): e.get("bullets", []) for e in out.get("experience", [])}
    for e in profile.get("experience", []):
        orig = e.get("bullets", [])
        bullets = [b for b in chosen.get(e["company"], []) if _nums(b) <= allowed_nums] or orig
        exp.append({**{k: e[k] for k in ("company", "title", "location", "dates") if k in e}, "bullets": bullets[:5]})
    summary = out.get("summary") or profile.get("summary", "")
    if not _nums(summary) <= allowed_nums:
        summary = profile.get("summary", "")
    cover = out.get("cover_letter") or (
        f"Dear Hiring Team at {job.company},\n\nI am applying for the {job.title} role. My background in "
        f"{', '.join(profile.get('skills', [])[:4])} aligns with your requirements, and I would welcome the chance to discuss it.\n\n"
        f"Regards,\n{profile['name']}")
    return {"summary": summary, "skills": skills, "experience": exp, "certifications": certs, "cover_letter": cover}

def render_pdf(t, profile, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    h = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=16, spaceAfter=2)
    sub = ParagraphStyle("s", fontName="Helvetica", fontSize=9, textColor="#444444", spaceAfter=8)
    sec = ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=10.5, spaceBefore=8, spaceAfter=3)
    body = ParagraphStyle("b", fontName="Helvetica", fontSize=9.5, leading=12.5)
    bul = ParagraphStyle("bl", parent=body, leftIndent=10, bulletIndent=0)
    esc = lambda x: (x or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = [Paragraph(esc(profile["name"]), h),
         Paragraph(esc(" | ".join(x for x in (profile.get("email"), profile.get("phone"), profile.get("location"), profile.get("linkedin")) if x)), sub),
         Paragraph("SUMMARY", sec), Paragraph(esc(t["summary"]), body),
         Paragraph("SKILLS", sec), Paragraph(esc(" • ".join(t["skills"])), body),
         Paragraph("EXPERIENCE", sec)]
    for e in t["experience"]:
        s.append(Paragraph(f"<b>{esc(e['title'])}</b>, {esc(e['company'])} — {esc(e.get('dates',''))}", body))
        s += [Paragraph(esc(b), bul, bulletText="•") for b in e["bullets"]]
        s.append(Spacer(1, 4))
    if profile.get("projects"):
        s.append(Paragraph("PROJECTS", sec))
        for p in profile["projects"][:3]:
            s.append(Paragraph(f"<b>{esc(p['name'])}</b> - {esc(p['description'])}", body))
            s.append(Spacer(1, 3))
    if t["certifications"]:
        s += [Paragraph("CERTIFICATIONS", sec), Paragraph(esc(" • ".join(t["certifications"])), body)]
    s.append(Paragraph("EDUCATION", sec))
    for ed in profile.get("education", []):
        s.append(Paragraph(esc(f"{ed['degree']}, {ed['institution']} ({ed.get('year','')})"), body))
    SimpleDocTemplate(path, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=15*mm, bottomMargin=15*mm).build(s)
    return path
