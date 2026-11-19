"""Works with either Claude (ANTHROPIC_API_KEY) or Google Gemini free tier (GEMINI_API_KEY).
Gemini is used automatically when only GEMINI_API_KEY is set. No extra packages needed for Gemini."""
import json, os, re, time
import requests

def provider():
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    return None

def _call(cfg, system, user, max_tokens):
    p = provider()
    if p is None:
        return None
    if p == "anthropic":
        import anthropic
        r = anthropic.Anthropic().messages.create(model=cfg["llm"]["model"], max_tokens=max_tokens, system=system,
                                                  messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in r.content if b.type == "text")
    model = cfg["llm"].get("gemini_model", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.3}}
    for attempt in range(4):  # free tier is rate limited: back off and retry
        r = requests.post(url, json=body, headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, timeout=90)
        if r.status_code == 429:
            time.sleep(15 * (attempt + 1))
            continue
        r.raise_for_status()
        parts = r.json()["candidates"][0]["content"]["parts"]
        time.sleep(7)  # stay under ~10 requests/minute on the free tier
        return "".join(x.get("text", "") for x in parts)
    raise RuntimeError("Gemini rate limit - try again later")

def ask_json(cfg, system, user, max_tokens=3000):
    text = _call(cfg, system, user, max_tokens)
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else None

def ask_text(cfg, system, user, max_tokens=500):
    text = _call(cfg, system, user, max_tokens)
    return text.strip() if text else None
