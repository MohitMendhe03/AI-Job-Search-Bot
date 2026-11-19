import datetime as dt

INDIA_CITIES = ["india", "ahmedabad", "vadodara", "baroda", "surat", "rajkot", "gandhinagar", "indore", "bhopal", "mumbai",
    "pune", "delhi", "noida", "gurgaon", "gurugram", "bengaluru", "bangalore", "hyderabad", "chennai", "kolkata",
    "jaipur", "chandigarh", "kochi", "coimbatore", "nagpur", "lucknow", "thane", "navi mumbai", "faridabad"]

def location_ok(loc, cfg):
    s = cfg["search"]
    l = (loc or "").lower()
    if any(c.lower() in l for c in s["locations"]) and not s["india_wide"]:
        return True
    if s["india_wide"] and any(c in l for c in INDIA_CITIES):
        return True
    if s.get("include_remote") and "remote" in l:
        return any(k in l for k in ("india", "worldwide", "anywhere", "apac", "asia")) or l.strip() in ("remote", "remote - ")
    return False

def role_ok(title, cfg):
    t = (title or "").lower()
    s = cfg["search"]
    if any(x.lower() in t.split() or f" {x.lower()} " in f" {t} " for x in s["exclude_title_keywords"]):
        return False
    return any(k.lower() in t for k in s["title_keywords"])

def fresh_ok(posted, hours):
    if not posted:
        return True
    try:
        d = dt.datetime.fromisoformat(posted.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return (dt.datetime.now(dt.timezone.utc) - d).total_seconds() <= hours * 3600
    except Exception:
        return True
