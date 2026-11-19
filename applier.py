"""Best-effort form filler for Greenhouse / Lever / Ashby using Playwright.
Form layouts differ per company, so selectors may need tuning. It NEVER solves CAPTCHAs:
those jobs are flagged for manual completion."""
import os, re, json
from llm import ask_text

APPLY_SUFFIX = {"lever": "/apply", "ashby": "/application", "greenhouse": ""}
FIELD_LABELS = [
    (r"first name", lambda p: p["name"].split()[0]),
    (r"last name|surname", lambda p: p["name"].split()[-1]),
    (r"^full name|^name\b", lambda p: p["name"]),
    (r"email", lambda p: p["email"]),
    (r"phone|mobile", lambda p: p["phone"]),
    (r"linkedin", lambda p: p.get("linkedin", "")),
    (r"current location|location|city", lambda p: p.get("location", "")),
]

def supported(job):
    return job.ats in APPLY_SUFFIX

def _answer(label, job, profile, cfg):
    l = label.lower()
    a = profile.get("answers", {})
    for key, val in (("notice", a.get("notice_period")), ("current ctc|current salary|current compensation", a.get("current_ctc")),
                     ("expected|salary expectation", a.get("expected_ctc")), ("authori|sponsor|visa", a.get("work_authorization")),
                     ("relocat", a.get("willing_to_relocate")), ("years of experience|total experience", a.get("total_experience_years"))):
        if val and re.search(key, l):
            return val
    if len(label) > 25:  # open-ended question -> ask the model, grounded in profile
        return ask_text(cfg, "Answer a job-application question in 2-4 sentences using ONLY facts from the profile. "
                        "If the profile lacks the facts, reply exactly: SKIP", f"PROFILE: {json.dumps(profile)}\nJOB: {job.title} at {job.company}\nQUESTION: {label}")
    return None

def apply(job, pdf_path, cover_letter, profile, cfg, submit=False, shot_dir="screenshots"):
    """Returns (status, note). status: applied | ready_for_review | captcha | manual | failed"""
    if not supported(job):
        return "manual", "No automatable form; apply manually using the tailored PDF."
    from playwright.sync_api import sync_playwright
    os.makedirs(shot_dir, exist_ok=True)
    shot = os.path.join(shot_dir, f"{job.id}.png")
    url = job.url.rstrip("/") + APPLY_SUFFIX[job.ats]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=cfg["apply"].get("headless", True))
        page = browser.new_page(viewport={"width": 1280, "height": 1800})
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2500)
            if page.locator("iframe[src*='recaptcha'], iframe[src*='hcaptcha'], .g-recaptcha, .h-captcha").count():
                page.screenshot(path=shot, full_page=True)
                return "captcha", "CAPTCHA present - complete manually."
            for pattern, getter in FIELD_LABELS:
                try:
                    el = page.get_by_label(re.compile(pattern, re.I)).first
                    val = getter(profile)
                    if val and el.count() and el.is_visible() and not el.input_value():
                        el.fill(val)
                except Exception:
                    pass
            files = page.locator("input[type=file]")
            if files.count():
                files.first.set_input_files(pdf_path)
            for el in page.locator("textarea:visible, input[type=text]:visible").all():
                try:
                    if el.input_value():
                        continue
                    label = el.evaluate("e => (e.labels && e.labels[0] ? e.labels[0].innerText : '') || e.getAttribute('aria-label') || ''").strip()
                    if not label:
                        continue
                    ans = _answer(label, job, profile, cfg)
                    if ans and ans.strip() != "SKIP":
                        el.fill(ans)
                except Exception:
                    pass
            page.screenshot(path=shot, full_page=True)
            if not submit:
                return "ready_for_review", f"Filled. Review screenshot: {shot}"
            page.get_by_role("button", name=re.compile(r"submit", re.I)).first.click()
            page.wait_for_timeout(5000)
            ok = re.search(r"thank|received|submitted", page.content(), re.I)
            page.screenshot(path=shot, full_page=True)
            return ("applied", "Submitted.") if ok else ("failed", "Clicked submit but no confirmation seen - check screenshot / form errors.")
        except Exception as e:
            return "failed", f"{type(e).__name__}: {str(e)[:120]}"
        finally:
            browser.close()
